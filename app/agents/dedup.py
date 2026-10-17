import math

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0  # Radius of Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def jaccard_similarity(str1: str, str2: str) -> float:
    words1 = set(str1.lower().split())
    words2 = set(str2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return len(intersection) / len(union)

def find_duplicate(new_lat: float, new_lon: float, new_desc: str, existing_tickets: list, radius_m: float = 50.0, sim_threshold: float = 0.20):
    for ticket in existing_tickets:
        dist = haversine_distance(new_lat, new_lon, ticket['latitude'], ticket['longitude'])
        sim = jaccard_similarity(new_desc, ticket['description'])
        if dist <= radius_m and sim >= sim_threshold:
            return ticket['token_id']
    return None
