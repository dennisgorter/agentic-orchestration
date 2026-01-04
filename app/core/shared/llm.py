"""LLM client wrapper for OpenAI API with retry/repair logic."""
import json
import os
import re
from typing import Any, Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError
from openai import OpenAI

from .models import IntentRequest, Car, ZoneCandidate, ZonePolicy, Decision


T = TypeVar('T', bound=BaseModel)


class LLMClient:
    """Wrapper for OpenAI API calls with structured output parsing."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable must be set")
        self.client = OpenAI(api_key=self.api_key)
        self.default_model = "gpt-4o-mini"
        self.fallback_model = "gpt-4o-mini"  # In real setup, use gpt-4 or similar as fallback
    
    def _call_llm(self, messages: list[dict], model: str, temperature: float = 0.7) -> str:
        """Make raw API call to OpenAI."""
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    
    def _parse_with_repair(
        self, 
        response_text: str, 
        model_class: Type[T],
        original_messages: list[dict],
        model: str
    ) -> T:
        """
        Attempt to parse response as JSON into model_class.
        If parsing fails, try to repair and retry.
        """
        # Try direct parse
        try:
            # Clean markdown code blocks if present
            cleaned = self._strip_markdown_json(response_text)
            data = json.loads(cleaned)
            return model_class.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            # Attempt repair: ask model to output ONLY valid JSON
            repair_messages = original_messages + [
                {"role": "assistant", "content": response_text},
                {
                    "role": "user",
                    "content": f"Your previous response could not be parsed. Error: {str(e)[:200]}. "
                               f"Please output ONLY valid JSON matching the required schema, with no additional text or markdown."
                }
            ]
            
            repaired_response = self._call_llm(repair_messages, model, temperature=0.3)
            
            try:
                cleaned = self._strip_markdown_json(repaired_response)
                data = json.loads(cleaned)
                return model_class.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as e2:
                # Last resort: try with fallback model
                if model != self.fallback_model:
                    return self._structured_call(original_messages, model_class, self.fallback_model)
                else:
                    raise ValueError(f"Failed to parse LLM response even after repair: {str(e2)}")
    
    def _strip_markdown_json(self, text: str) -> str:
        """Remove markdown code block markers from JSON response."""
        # Remove ```json ... ``` or ``` ... ```
        text = re.sub(r'^```(?:json)?\s*\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n```\s*$', '', text, flags=re.MULTILINE)
        return text.strip()
    
    def _structured_call(
        self, 
        messages: list[dict], 
        model_class: Type[T],
        model: Optional[str] = None
    ) -> T:
        """
        Make LLM call expecting structured JSON response.
        Includes retry and repair logic.
        """
        if model is None:
            model = self.default_model
        
        response_text = self._call_llm(messages, model)
        return self._parse_with_repair(response_text, model_class, messages, model)
    
    def call_detect_language(self, user_message: str) -> str:
        """
        Detect the language of the user message.
        
        Returns ISO 639-1 language code (e.g., 'en', 'es', 'fr', 'nl', 'de').
        """
        prompt = f"""Detect the language of the following user message and return ONLY the ISO 639-1 two-letter language code.

Common codes:
- en: English
- es: Spanish
- fr: French
- nl: Dutch
- de: German
- it: Italian
- pt: Portuguese

User message: "{user_message}"

Respond with ONLY the two-letter language code, nothing else."""
        
        messages = [
            {"role": "system", "content": "You are a language detection assistant. Respond only with the ISO 639-1 language code."},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_llm(messages, self.default_model, temperature=0.3)
        # Extract just the language code (in case LLM adds extra text)
        lang_code = response.strip().lower()[:2]
        # Default to English if detection fails
        if not lang_code.isalpha() or len(lang_code) != 2:
            return "en"
        return lang_code
    
    def call_translate_message(self, message: str, language: str) -> str:
        """
        Translate a simple message to the target language.
        
        Args:
            message: The message to translate
            language: ISO 639-1 language code for target language
        
        Returns:
            Translated message
        """
        if language == "en":
            return message
        
        prompt = f"""Translate the following message to the language with ISO 639-1 code: {language}

Message: "{message}"

Respond with ONLY the translated message, nothing else."""
        
        messages = [
            {"role": "system", "content": "You are a translation assistant. Translate concisely and accurately."},
            {"role": "user", "content": prompt}
        ]
        
        return self._call_llm(messages, self.default_model, temperature=0.3)
    
    def call_extract_intent_slots(self, user_message: str) -> IntentRequest:
        """
        Extract intent and slots from user message.
        
        Returns IntentRequest with intent type and extracted slots.
        """
        prompt = f"""You are an intent classifier for a car pollution zone eligibility service.

Analyze the user's message and extract:
1. intent: one of "single_car", "fleet", or "policy_only"
   - single_car: user asks about ONE specific car
   - fleet: user asks about ALL/MULTIPLE cars (e.g., "which of my cars", "are any of my cars")
   - policy_only: user only asks about zone rules, no specific car

2. car_identifier: plate number or identifying phrase (null if not mentioned or if fleet/policy_only)
3. city: city name (null if not mentioned)
4. zone_phrase: phrase describing the zone (e.g., "city center", "downtown", null if not mentioned)

User message: "{user_message}"

Respond with ONLY valid JSON matching this schema:
{{
  "intent": "single_car" | "fleet" | "policy_only",
  "car_identifier": string or null,
  "city": string or null,
  "zone_phrase": string or null
}}"""
        
        messages = [
            {"role": "system", "content": "You are a precise intent extraction assistant. Always respond with valid JSON only."},
            {"role": "user", "content": prompt}
        ]
        
        return self._structured_call(messages, IntentRequest)
    
    def call_make_disambiguation_question(
        self, 
        kind: str,  # "car" or "zone"
        options: list[dict],
        language: str = "en"
    ) -> str:
        """
        Generate a natural disambiguation question.
        
        Args:
            kind: "car" or "zone"
            options: list of dicts with keys like "label", "plate", "zone_name", etc.
            language: ISO 639-1 language code for response language
        
        Returns:
            A short, clear question asking user to choose.
        """
        if kind == "car":
            cars_list = "\n".join([f"{i+1}. {opt['label']}" for i, opt in enumerate(options)])
            prompt = f"""You have multiple cars on file. Generate a SHORT question (one sentence) asking the user to choose which car they're asking about.

Available cars:
{cars_list}

Respond in the language with ISO 639-1 code: {language}
Generate ONLY the question text, no extra formatting."""
        else:  # zone
            zones_list = "\n".join([f"{i+1}. {opt['label']}" for i, opt in enumerate(options)])
            prompt = f"""Multiple pollution zones match the user's query. Generate a SHORT question (one sentence) asking them to specify which zone.

Matching zones:
{zones_list}

Respond in the language with ISO 639-1 code: {language}
Generate ONLY the question text, no extra formatting."""
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Be concise and clear."},
            {"role": "user", "content": prompt}
        ]
        
        return self._call_llm(messages, self.default_model, temperature=0.7)
    
    def call_explain(
        self,
        intent: str,
        decision: Optional[Decision] = None,
        fleet_decisions: Optional[list] = None,
        car: Optional[Car] = None,
        cars: Optional[list[Car]] = None,
        policy: Optional[ZonePolicy] = None,
        zone: Optional[ZoneCandidate] = None,
        language: str = "en"
    ) -> str:
        """
        Generate final explanation grounded in decision and facts.
        
        Args:
            intent: "single_car", "fleet", or "policy_only"
            decision: Decision object for single car
            fleet_decisions: List of FleetDecision for fleet queries
            car: Single car object
            cars: List of cars for fleet
            policy: Zone policy
            zone: Zone candidate
            language: ISO 639-1 language code for response language
        
        Returns:
            Clear, user-friendly explanation.
        """
        if intent == "policy_only":
            prompt = f"""Explain the pollution zone policy to the user in a clear, friendly way.

Zone: {zone.zone_name if zone else 'Unknown'}
City: {zone.city if zone else 'Unknown'}
Type: {zone.zone_type if zone else 'Unknown'}

Policy effective from: {policy.effective_from if policy else 'Unknown'}
Rules:
{chr(10).join([f"- {rule.condition}: {rule.verdict}" for rule in (policy.rules if policy else [])]) if policy else 'No rules available'}

Exemptions: {', '.join(policy.exemptions) if policy and policy.exemptions else 'None'}

IMPORTANT: Respond in the language with ISO 639-1 code: {language}
Provide a 2-3 sentence summary suitable for a chatbot response.
Then append a helpful note: mention that they can get a specific eligibility check for their vehicle by providing their car's plate number or VIN."""
        
        elif intent == "single_car":
            prompt = f"""Explain the eligibility decision to the user clearly and concisely.

Car: {car.plate if car else 'Unknown'} ({car.fuel_type if car and car.fuel_type else 'unknown fuel'}, {car.euro_class if car and car.euro_class else 'unknown euro class'})
Zone: {zone.zone_name if zone else 'Unknown'}
Allowed: {decision.allowed if decision else 'unknown'}
Reason: {decision.reason_code if decision else 'unknown'}
Factors: {', '.join(decision.factors) if decision and decision.factors else 'None'}
Missing fields: {', '.join(decision.missing_fields) if decision and decision.missing_fields else 'None'}
Next actions: {', '.join(decision.next_actions) if decision and decision.next_actions else 'None'}

IMPORTANT: Respond in the language with ISO 639-1 code: {language}
Provide a clear 2-4 sentence explanation suitable for a chatbot response. If there are missing fields or next actions, mention them."""
        
        else:  # fleet
            allowed_cars = [fd for fd in fleet_decisions if fd.decision.allowed == "true"] if fleet_decisions else []
            banned_cars = [fd for fd in fleet_decisions if fd.decision.allowed == "false"] if fleet_decisions else []
            unknown_cars = [fd for fd in fleet_decisions if fd.decision.allowed == "unknown"] if fleet_decisions else []
            
            prompt = f"""Summarize the fleet eligibility check for the user.

Zone: {zone.zone_name if zone else 'Unknown'}
Total cars checked: {len(fleet_decisions) if fleet_decisions else 0}
Allowed: {len(allowed_cars)} ({', '.join([fd.plate for fd in allowed_cars]) if allowed_cars else 'none'})
Not allowed: {len(banned_cars)} ({', '.join([fd.plate for fd in banned_cars]) if banned_cars else 'none'})
Unknown: {len(unknown_cars)} ({', '.join([fd.plate for fd in unknown_cars]) if unknown_cars else 'none'})

IMPORTANT: Respond in the language with ISO 639-1 code: {language}
Provide a clear summary suitable for a chatbot response. List cars by category (allowed, not allowed, unknown) and mention why if relevant."""
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant explaining car pollution zone eligibility. Be clear, concise, and friendly."},
            {"role": "user", "content": prompt}
        ]
        
        return self._call_llm(messages, self.default_model, temperature=0.7)


# Global instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create global LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
