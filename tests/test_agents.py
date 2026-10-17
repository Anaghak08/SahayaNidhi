import unittest
from app.agents.dedup import haversine_distance, jaccard_similarity, find_duplicate

class TestMember3Agents(unittest.TestCase):
    def test_haversine(self):
        dist = haversine_distance(12.97160, 77.59460, 12.97162, 77.59461)
        self.assertLess(dist, 50.0)

    def test_jaccard(self):
        sim = jaccard_similarity("Open drain near bus stop", "Uncovered drain at bus stop")
        self.assertGreaterEqual(sim, 0.20)

    def test_find_duplicate(self):
        tickets = [{'token_id': 'TK-1001', 'latitude': 12.97160, 'longitude': 77.59460, 'description': 'Open drain near bus stop'}]
        dup = find_duplicate(12.97162, 77.59461, "Uncovered drain near bus stop", tickets)
        self.assertEqual(dup, 'TK-1001')

if __name__ == '__main__':
    unittest.main()
