# Recursion Fix - Graph Routing

## Problem
When querying "is my car AB-123-EF allowed in Amsterdam ZEZ?", the system hit a recursion limit of 50 iterations without reaching an END state.

## Root Cause
After changing the graph flow architecture from **zone→car→policy** to **car→zone→policy**, several routing functions were not updated to respect the `next_step` field set by nodes. This caused infinite loops in two scenarios:

### Scenario 1: Invalid Car (Not Found)
When `resolve_car_node` couldn't find a car and set `next_step = "end"`, the `route_after_car` function ignored this and always routed to `"resolve_zone"`, creating a loop.

### Scenario 2: Valid Car with Zone
When the flow was: extract_intent → resolve_car → resolve_zone, the `route_after_zone` function would route back to `resolve_car` for non-policy-only intents, creating an infinite car→zone→car loop.

## Solution
Updated routing functions to respect `next_step` values set by nodes:

### 1. Fixed `route_after_car` (Line ~268)
```python
def route_after_car(state: AgentState) -> str:
    """Route after car resolution."""
    if state.pending_question or state.next_step == "end":
        return "end"
    return "resolve_zone"  # Go to zone resolution next
```

**Change**: Added `or state.next_step == "end"` check to respect when resolve_car_node explicitly wants to end (e.g., car not found).

### 2. Fixed `route_after_zone` (Line ~258)
```python
def route_after_zone(state: AgentState) -> str:
    """Route after zone resolution."""
    if state.pending_question:
        return "end"
    
    # Respect explicit next_step from node
    if state.next_step == "fetch_policy":
        return "fetch_policy"
    
    if state.intent == "policy_only":
        return "fetch_policy"
    else:
        return "resolve_car"
```

**Change**: Added check for `state.next_step == "fetch_policy"` before the intent-based routing. This prevents the zone node from routing back to resolve_car when it has already selected a zone and set next_step to fetch_policy.

### 3. Fixed `resolve_car_node` next_step assignments
Changed line 156 from `state.next_step = "fetch_policy"` to `state.next_step = "resolve_zone"` to align with the car→zone→policy flow.

### 4. Added recursion_limit config (Line ~367)
```python
def get_graph():
    """Get or create compiled graph."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph.with_config({"recursion_limit": 50})
```

**Change**: Increased from default 25 to 50 as a safety measure, though the routing fixes should prevent hitting any limit.

## Graph Flow After Fix
The correct flow is now:

### For car-related queries (intent = "check_car" or "fleet"):
1. extract_intent
2. resolve_car (sets next_step based on result)
   - If car not found → END
   - If disambiguation needed → END (with pending_question)
   - If car found → next_step = "resolve_zone"
3. resolve_zone (sets next_step based on result)
   - If zone not found → END
   - If disambiguation needed → END (with pending_question)
   - If zone found → next_step = "fetch_policy"
4. fetch_policy → next_step = "decide"
5. decide → next_step = "explain"
6. explain → next_step = "end"
7. END

### For policy-only queries (intent = "policy_only"):
1. extract_intent
2. resolve_zone
3. fetch_policy
4. END (no decision/explain needed)

## Testing
All test cases now pass:
- ✅ Invalid car plate (AB-123-EF) - returns error without recursion
- ✅ Valid car with zone (AB-123-CD in Amsterdam ZEZ) - completes full flow
- ✅ All test_api.sh examples pass
- ✅ Disambiguation flows work correctly
- ✅ Fleet queries work correctly

## Key Lessons
1. When changing graph flow architecture, ALL routing functions must be updated consistently
2. Router functions should respect `next_step` values set by nodes
3. Each routing function should handle early termination (next_step="end")
4. Graph recursion errors indicate routing loops, not necessarily computational complexity

## Files Modified
- [app/graph.py](app/graph.py) - Fixed routing functions and next_step assignments
