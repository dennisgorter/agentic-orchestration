"""Mock services for car info and city policy (in-memory stubs)."""
from datetime import date
from typing import Optional
from app.core.shared.models import Car, ZoneCandidate, ZonePolicy, ZonePolicyRule


# ========== Mock Data ==========

MOCK_CARS = {
    "session_default": [
        Car(
            car_id="car_001",
            plate="AB-123-CD",
            fuel_type="diesel",
            euro_class="euro4",
            first_reg_date=date(2010, 3, 15),
            vehicle_category="M1"
        ),
        Car(
            car_id="car_002",
            plate="EF-456-GH",
            fuel_type="petrol",
            euro_class="euro5",
            first_reg_date=date(2015, 7, 22),
            vehicle_category="M1"
        ),
        Car(
            car_id="car_003",
            plate="IJ-789-KL",
            fuel_type="electric",
            euro_class=None,
            first_reg_date=date(2021, 1, 10),
            vehicle_category="M1"
        ),
        Car(
            car_id="car_004",
            plate="MN-321-OP",
            fuel_type="diesel",
            euro_class="euro6",
            first_reg_date=date(2018, 11, 5),
            vehicle_category="N1"
        ),
    ]
}

MOCK_ZONES = {
    "amsterdam": [
        ZoneCandidate(
            city="Amsterdam",
            zone_id="ams_lez_01",
            zone_name="Amsterdam City Center LEZ",
            zone_type="LEZ"
        ),
        ZoneCandidate(
            city="Amsterdam",
            zone_id="ams_zez_01",
            zone_name="Amsterdam Logistics ZEZ",
            zone_type="ZEZ"
        ),
    ],
    "rotterdam": [
        ZoneCandidate(
            city="Rotterdam",
            zone_id="rtd_lez_01",
            zone_name="Rotterdam Environmental Zone",
            zone_type="LEZ"
        ),
    ],
}

MOCK_POLICIES = {
    "ams_lez_01": ZonePolicy(
        city="Amsterdam",
        zone_id="ams_lez_01",
        zone_name="Amsterdam City Center LEZ",
        effective_from=date(2020, 1, 1),
        rules=[
            ZonePolicyRule(
                condition="Diesel passenger cars (M1) with Euro class 4 or lower",
                verdict="banned",
                applies_to=["diesel", "euro4", "M1"]
            ),
            ZonePolicyRule(
                condition="Diesel passenger cars (M1) with Euro class 3 or lower",
                verdict="banned",
                applies_to=["diesel", "euro3", "M1"]
            ),
        ],
        exemptions=["vintage_cars", "disabled_permit"]
    ),
    "ams_zez_01": ZonePolicy(
        city="Amsterdam",
        zone_id="ams_zez_01",
        zone_name="Amsterdam Logistics ZEZ",
        effective_from=date(2025, 1, 1),
        rules=[
            ZonePolicyRule(
                condition="Light commercial vehicles (N1) must be zero-emission (BEV)",
                verdict="banned",
                applies_to=["N1", "non_electric"]
            ),
        ],
        exemptions=[]
    ),
    "rtd_lez_01": ZonePolicy(
        city="Rotterdam",
        zone_id="rtd_lez_01",
        zone_name="Rotterdam Environmental Zone",
        effective_from=date(2019, 6, 1),
        rules=[
            ZonePolicyRule(
                condition="Diesel vehicles with Euro class 3 or lower",
                verdict="banned",
                applies_to=["diesel", "euro3"]
            ),
        ],
        exemptions=["emergency_vehicles"]
    ),
}


# ========== Mock Service Functions ==========

def list_user_cars(session_id: str) -> list[Car]:
    """Return list of cars for a user/session."""
    # For PoC, all sessions get the same default car list
    return MOCK_CARS.get(session_id, MOCK_CARS["session_default"])


def resolve_zone(city: str, zone_phrase: Optional[str] = None) -> list[ZoneCandidate]:
    """
    Resolve city + optional zone phrase to zone candidates.
    
    If zone_phrase contains "center", "downtown", or is None, return all zones.
    In a real system, this would do fuzzy matching.
    """
    city_lower = city.lower()
    candidates = MOCK_ZONES.get(city_lower, [])
    
    if not zone_phrase:
        return candidates
    
    # Simple keyword matching
    phrase_lower = zone_phrase.lower()
    if "center" in phrase_lower or "downtown" in phrase_lower:
        # Multiple zones might match "city center"
        return candidates
    elif "logistic" in phrase_lower or "cargo" in phrase_lower or "zez" in phrase_lower:
        return [c for c in candidates if c.zone_type == "ZEZ"]
    elif "lez" in phrase_lower or "emission" in phrase_lower:
        return [c for c in candidates if c.zone_type == "LEZ"]
    
    return candidates


def get_policy(zone_id: str) -> Optional[ZonePolicy]:
    """Get policy for a specific zone."""
    return MOCK_POLICIES.get(zone_id)


def find_car_by_identifier(cars: list[Car], identifier: str) -> list[Car]:
    """
    Find cars matching an identifier (plate number or partial match).
    Returns list of matching cars.
    """
    identifier_lower = identifier.lower().replace("-", "").replace(" ", "")
    matches = []
    
    for car in cars:
        plate_normalized = car.plate.lower().replace("-", "").replace(" ", "")
        if identifier_lower in plate_normalized or plate_normalized in identifier_lower:
            matches.append(car)
    
    return matches
