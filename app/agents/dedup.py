import math
import re

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS points in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    
    return R * c

def text_similarity(text1: str, text2: str) -> float:
    """Calculates Jaccard word overlap ratio (0.0 to 1.0)."""
    words1 = set(re.findall(r'\w+', text1.lower()))
    words2 = set(re.findall(r'\w+', text2.lower()))
    
    if not words1 or not words2:
        return 0.0
        
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)

def find_duplicate(db_conn, category: str, lat: float, lon: float, description: str, radius_m: float = 50.0, sim_threshold: float = 0.20):
    """Queries active tokens within 50m radius and 0.20 similarity threshold."""
    cursor = db_conn.cursor()
    
    cursor.execute("""
        SELECT token_id, incident_id, description, category, latitude, longitude, status 
        FROM tokens 
        WHERE status IN ('NEW', 'ASSIGNED', 'IN_PROGRESS') AND category = ?
    """, (category,))
    
    existing_tokens = cursor.fetchall()
    
    for row in existing_tokens:
        t_id, inc_id, t_desc, t_cat, t_lat, t_lon, t_status = row
        
        if t_lat is not None and t_lon is not None:
            dist = haversine_distance(lat, lon, float(t_lat), float(t_lon))
            sim = text_similarity(description, t_desc)
            
            if dist <= radius_m and sim >= sim_threshold:
                return {
                    "is_duplicate": True,
                    "master_token_id": t_id,
                    "incident_id": inc_id,
                    "distance_meters": round(dist, 2),
                    "similarity_score": round(sim, 2)
                }
                
    return {"is_duplicate": False, "master_token_id": None}
