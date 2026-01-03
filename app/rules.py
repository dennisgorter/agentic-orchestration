"""Deterministic eligibility decision logic."""
from datetime import date
from typing import Optional
from app.models import Car, ZonePolicy, Decision


def decide_eligibility(
    car: Car,
    policy: ZonePolicy,
    check_date: Optional[date] = None
) -> Decision:
    """
    Deterministically decide if a car is allowed in a zone.
    
    Returns a Decision with allowed status, reason code, factors, 
    missing fields, and next actions.
    """
    if check_date is None:
        check_date = date.today()
    
    # Check if we have required fields
    missing = []
    if not car.fuel_type:
        missing.append("fuel_type")
    if not car.vehicle_category:
        missing.append("vehicle_category")
    
    # For non-electric vehicles, euro class is typically required
    if car.fuel_type and car.fuel_type.lower() != "electric" and not car.euro_class:
        missing.append("euro_class")
    
    if missing:
        return Decision(
            allowed="unknown",
            reason_code="MISSING_VEHICLE_DATA",
            factors=[],
            missing_fields=missing,
            next_actions=[f"Please provide {', '.join(missing)} for vehicle {car.plate}"]
        )
    
    # Check policy effective date
    if check_date < policy.effective_from:
        return Decision(
            allowed="true",
            reason_code="POLICY_NOT_YET_EFFECTIVE",
            factors=[f"Policy effective from {policy.effective_from}"],
            missing_fields=[],
            next_actions=[]
        )
    
    # Apply rules
    factors = []
    banned = False
    matching_rules = []
    
    for rule in policy.rules:
        if rule.verdict == "banned":
            # Check if rule applies to this car
            applies = _rule_applies(car, rule)
            if applies:
                matching_rules.append(rule)
                factors.append(f"Matches rule: {rule.condition}")
                banned = True
    
    if banned:
        return Decision(
            allowed="false",
            reason_code="BANNED_BY_POLICY",
            factors=factors,
            missing_fields=[],
            next_actions=[
                f"Vehicle does not meet {policy.zone_name} requirements",
                "Consider using an alternative vehicle or public transportation"
            ]
        )
    
    # Allowed
    return Decision(
        allowed="true",
        reason_code="MEETS_REQUIREMENTS",
        factors=[f"Vehicle meets all requirements for {policy.zone_name}"],
        missing_fields=[],
        next_actions=[]
    )


def _rule_applies(car: Car, rule) -> bool:
    """Check if a policy rule applies to a given car."""
    applies_to = rule.applies_to
    
    # Check fuel type
    if car.fuel_type and car.fuel_type.lower() in [a.lower() for a in applies_to]:
        # Check vehicle category
        if car.vehicle_category and car.vehicle_category in applies_to:
            # Check euro class
            if car.euro_class and car.euro_class.lower() in [a.lower() for a in applies_to]:
                return True
            # If no euro class specified in rule, just fuel + category match
            if not any(a.lower().startswith("euro") for a in applies_to):
                return True
    
    # Special case: N1 non-electric rule (for ZEZ)
    if "N1" in applies_to and "non_electric" in applies_to:
        if car.vehicle_category == "N1" and car.fuel_type and car.fuel_type.lower() != "electric":
            return True
    
    # Check if euro class alone matches (for broader bans)
    if car.euro_class:
        euro_lower = car.euro_class.lower()
        if euro_lower in [a.lower() for a in applies_to]:
            # Check fuel type match too
            if car.fuel_type and car.fuel_type.lower() in [a.lower() for a in applies_to]:
                return True
            # Euro3 and below might ban all fuels
            if euro_lower in ["euro3", "euro2", "euro1", "euro0"]:
                if "diesel" in [a.lower() for a in applies_to] and car.fuel_type and car.fuel_type.lower() == "diesel":
                    return True
    
    return False
