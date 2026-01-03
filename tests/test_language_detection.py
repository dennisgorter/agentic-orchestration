#!/usr/bin/env python3
"""
Test script for language detection feature.
Demonstrates that the system can detect user's language and respond accordingly.
"""
import os
import sys
from app.llm import get_llm_client

# Ensure OPENAI_API_KEY is set
if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY environment variable not set")
    sys.exit(1)


def test_language_detection():
    """Test language detection with various messages."""
    
    test_cases = [
        ("Can I drive my diesel car in Amsterdam city center?", "en"),
        ("¿Puedo conducir mi coche diésel en el centro de Madrid?", "es"),
        ("Puis-je conduire ma voiture diesel dans le centre de Paris?", "fr"),
        ("Kan ik met mijn dieselauto in het centrum van Amsterdam rijden?", "nl"),
        ("Darf ich mit meinem Dieselauto in die Berliner Innenstadt fahren?", "de"),
        ("Posso guidare la mia auto diesel nel centro di Roma?", "it"),
    ]
    
    print("Testing Language Detection")
    print("=" * 60)
    
    llm = get_llm_client()
    
    for message, expected_lang in test_cases:
        detected_lang = llm.call_detect_language(message)
        status = "✓" if detected_lang == expected_lang else "✗"
        
        print(f"\n{status} Message: {message}")
        print(f"  Expected: {expected_lang}, Detected: {detected_lang}")
    
    print("\n" + "=" * 60)
    print("\nTesting Message Translation")
    print("=" * 60)
    
    # Test translation
    test_message = "I couldn't find any pollution zones in the specified city. Please check the city name."
    
    languages = ["en", "es", "fr", "nl", "de"]
    
    for lang in languages:
        translated = llm.call_translate_message(test_message, lang)
        print(f"\n[{lang.upper()}]: {translated}")
    
    print("\n" + "=" * 60)
    print("Language detection test completed!")


if __name__ == "__main__":
    test_language_detection()
