import unittest
from app.agents.dedup import haversine_distance, text_similarity

class TestMember3Logic(unittest.TestCase):
    
    def test_haversine_distance_within_radius(self):
        # Two GPS points ~20 meters apart
        dist = haversine_distance(12.97160, 77.59460, 12.97162, 77.59461)
        self.assertLess(dist, 50.0)
        
    def test_haversine_distance_outside_radius(self):
        # Two GPS points > 500 meters apart
        dist = haversine_distance(12.97160, 77.59460, 12.97600, 77.60000)
        self.assertGreater(dist, 50.0)
        
    def test_text_similarity(self):
        desc1 = "Open drain near bus stop"
        desc2 = "Open drain uncovered near bus stop"
        sim = text_similarity(desc1, desc2)
        self.assertGreaterEqual(sim, 0.20)

if __name__ == "__main__":
    unittest.main()
