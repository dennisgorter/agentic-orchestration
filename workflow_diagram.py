"""
Agent Orchestrator - Workflow Visualization

This module provides a visual representation of the LangGraph workflow.
Run this script to generate a diagram (requires graphviz).
"""

from app.graph import build_graph


def print_workflow_ascii():
    """Print ASCII representation of the workflow."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     AGENT ORCHESTRATOR WORKFLOW                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌─────────────────┐
│  User Message   │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│  Extract Intent     │  ◄── LLM Call (OpenAI)
│  • single_car       │      Extracts: intent, car_id, city, zone_phrase
│  • fleet            │
│  • policy_only      │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Resolve Zone       │  ◄── Mock Service (resolve_zone)
│  • city → zones     │      Returns zone candidates
│  • zone_phrase      │
└─────────┬───────────┘
          │
          ├──────────────── Multiple zones? ────────────────┐
          │                                                  │
          │ Single zone                                      │ Yes
          ▼                                                  ▼
          │                                      ┌─────────────────────┐
          │                                      │ Disambiguation      │  ◄── LLM Call
          │                                      │ Question (Zone)     │      (phrasing)
          │                                      └──────────┬──────────┘
          │                                                 │
          │                                                 ▼
          │                                          [Wait for Answer]
          │                                                 │
          │ ◄───────────────────────────────────────────────┘
          │
          ▼
    ┌─────────┐
    │ Intent? │
    └────┬────┘
         │
    ┌────┼─────────────────────────┐
    │    │                         │
    │    │                         │
    ▼    ▼                         ▼
 single  fleet                 policy_only
  car                               │
    │    │                          │
    │    │                          ▼
    │    │                   [Skip to Fetch Policy]
    │    │
    │    ▼
    │ ┌─────────────────────┐
    │ │ Resolve Car(s)      │  ◄── Mock Service (list_user_cars)
    │ │ • fleet: all cars   │      Returns car list
    │ │ • single: find car  │
    │ └─────────┬───────────┘
    │           │
    │           ├──────── Multiple cars? ──────────────┐
    │           │                                       │
    │           │ Single car                            │ Yes
    │           ▼                                       ▼
    │           │                           ┌─────────────────────┐
    │           │                           │ Disambiguation      │  ◄── LLM Call
    │           │                           │ Question (Car)      │      (phrasing)
    │           │                           └──────────┬──────────┘
    │           │                                      │
    │           │                                      ▼
    │           │                               [Wait for Answer]
    │           │                                      │
    │           │ ◄────────────────────────────────────┘
    ▼           ▼
    └───────┬───┘
            │
            ▼
┌─────────────────────┐
│  Fetch Policy       │  ◄── Mock Service (get_policy)
│  • zone_id → policy │      Returns ZonePolicy with rules
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Decide Eligibility │  ◄── Pure Python (decide_eligibility)
│  • Apply rules      │      Deterministic logic
│  • Check exemptions │      NO LLM involvement
│  • Missing fields?  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Explain Result     │  ◄── LLM Call (OpenAI)
│  • Generate natural │      Grounded in facts from Decision
│    language response│
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Return to User     │
│  • reply text       │
│  • pending_question │
│  • options (if any) │
└─────────────────────┘


╔══════════════════════════════════════════════════════════════════════════════╗
║                          KEY DECISION POINTS                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

1. Multiple Zones Match:
   → Ask user to pick specific zone (LEZ vs ZEZ, etc.)

2. Multiple Cars Match (or no car_identifier in single_car intent):
   → Ask user to pick specific car

3. Missing Vehicle Fields (fuel_type, euro_class, vehicle_category):
   → Return Decision with allowed="unknown" and list missing_fields

4. Fleet Query:
   → Process all cars, group results by allowed/banned/unknown


╔══════════════════════════════════════════════════════════════════════════════╗
║                            LLM RESPONSIBILITIES                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

✓ Intent + Slot Extraction
  - Parse user message → structured IntentRequest
  - Extract: intent type, car identifier, city, zone phrase

✓ Disambiguation Question Phrasing
  - Generate natural question when multiple options exist
  - Keep it concise (1 sentence)

✓ Final Explanation
  - Convert Decision + facts → user-friendly response
  - Grounded in deterministic decision, never overrides it


╔══════════════════════════════════════════════════════════════════════════════╗
║                          DETERMINISTIC COMPONENTS                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

✓ Zone Resolution (tools.py)
  - City + phrase → zone candidates
  - Fuzzy matching on zone names/types

✓ Car Resolution (tools.py)
  - Identifier → matching cars
  - Plate number normalization

✓ Policy Fetch (tools.py)
  - zone_id → ZonePolicy with rules

✓ Eligibility Decision (rules.py)
  - Car + Policy → Decision (allowed/banned/unknown)
  - Pure business logic, NO LLM
  - Example rules:
    * Diesel Euro 4 banned in Amsterdam LEZ
    * N1 vehicles must be electric in ZEZ


╔══════════════════════════════════════════════════════════════════════════════╗
║                               STATE MANAGEMENT                               ║
╚══════════════════════════════════════════════════════════════════════════════╝

AgentState tracks:
  - Extracted slots (intent, car_identifier, city, zone_phrase)
  - Resolved entities (cars, selected_car, zones, selected_zone, policy)
  - Decisions (decision, fleet_decisions)
  - Disambiguation (pending_question, pending_type, options)
  - Control flow (next_step, reply)

Stored in-memory by session_id for PoC.
Production: Use Redis or database.
""")


if __name__ == "__main__":
    print_workflow_ascii()
    print("\n\n")
    print("To visualize the actual LangGraph:")
    print("  1. Install graphviz: brew install graphviz (macOS) or apt-get install graphviz (Linux)")
    print("  2. pip install pygraphviz")
    print("  3. Run: python -c 'from app.graph import build_graph; g = build_graph(); g.get_graph().draw_mermaid()'")
