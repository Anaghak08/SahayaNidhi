import math
from typing import Dict, Any, List, Optional


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points
    on the earth in meters.
    """
    R = 6371000.0  # Earth radius in meters

    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    delta_phi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lon2) - float(lon1))

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return R * c


def verify_repair(
    after_image_hash: Optional[str] = None,
    ticket_lat: Optional[float] = None,
    ticket_lon: Optional[float] = None,
    worker_lat: Optional[float] = None,
    worker_lon: Optional[float] = None,
    completion_notes: Optional[str] = None,
    worker_confirmed: bool = False,
    max_allowed_radius_m: float = 30.0,
    min_notes_length: int = 10,
    **kwargs
) -> Dict[str, Any]:
    """
    Agent 4: Repair Evidence Verification.
    Matches positional order:
    (after_image_hash, ticket_lat, ticket_lon, worker_lat, worker_lon, completion_notes, worker_confirmed)
    """
    reasons: List[str] = []

    # 1. After-photo presence
    if not after_image_hash or not str(after_image_hash).strip():
        reasons.append("MISSING_AFTER_PHOTO")

    # 2. Worker GPS presence
    if worker_lat is None or worker_lon is None:
        reasons.append("MISSING_WORKER_GPS")
    else:
        # 3. GPS Proximity (within 30m)
        if ticket_lat is not None and ticket_lon is not None:
            try:
                dist = haversine_distance_meters(
                    float(ticket_lat), float(ticket_lon),
                    float(worker_lat), float(worker_lon)
                )
                if dist > max_allowed_radius_m:
                    reasons.append("GPS_OUTSIDE_ALLOWED_RADIUS")
            except (ValueError, TypeError):
                reasons.append("INVALID_GPS_COORDINATES")

    # 4. Completion notes length
    notes_clean = (completion_notes or "").strip()
    if len(notes_clean) < min_notes_length:
        reasons.append("COMPLETION_NOTES_TOO_SHORT")

    # 5. Worker attestation
    if not worker_confirmed:
        reasons.append("WORKER_DID_NOT_CONFIRM_REPAIR")

    if not reasons:
        return {
            "status": "PASS",
            "confidence": 0.95,
            "reasons": []
        }
    else:
        return {
            "status": "REVIEW",
            "confidence": 0.35,
            "reasons": reasons
        }
