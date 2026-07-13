import unittest
import scoring_engine

class TestScoringEngine(unittest.TestCase):

    def test_detect_filler_words(self):
        text = "So, like, machine learning is um, basically artificial intelligence you know."
        # Fillers expected: "so" (1), "like" (1), "um" (1), "basically" (1), "you know" (1)
        count = scoring_engine.detect_filler_words(text)
        self.assertEqual(count, 5)
        
        text_clean = "Machine learning is a branch of computer science."
        self.assertEqual(scoring_engine.detect_filler_words(text_clean), 0)

    def test_calculate_scores_strong(self):
        # Scenario: Excellent explanation, natural flow, optimal speed (130 WPM), 1 pause, 0 fillers
        res = scoring_engine.calculate_scores(
            semantic_similarity=0.85,
            keyword_coverage=0.90,
            pause_ratio=0.15,
            filler_count=0,
            duration_sec=15.0,
            word_count=32.0  # 32 / 15 * 60 = 128 WPM
        )
        
        self.assertEqual(res["understanding_level"], "Strong Understanding")
        self.assertGreaterEqual(res["overall_score"], 80.0)
        self.assertIn("Natural, conversational speaking pace", "".join(res["strengths"]))
        self.assertEqual(res["metrics"]["filler_count"], 0)

    def test_calculate_scores_moderate_rushed(self):
        # Scenario: Decent similarity (0.6), coverage (0.6), but rushed pacing (170 WPM) and very low pauses (3%)
        res = scoring_engine.calculate_scores(
            semantic_similarity=0.60,
            keyword_coverage=0.60,
            pause_ratio=0.03,
            filler_count=2,
            duration_sec=10.0,
            word_count=28.0  # 28 / 10 * 60 = 168 WPM
        )
        
        self.assertEqual(res["understanding_level"], "Moderate Understanding")
        self.assertLess(res["metrics"]["pause_score"], 100.0)
        self.assertTrue(any("pace is fast" in imp or "low pause ratio" in imp for imp in res["improvements"]))

    def test_calculate_scores_poor_hesitant(self):
        # Scenario: Poor similarity (0.3), coverage (0.2), slow pace (50 WPM), high pauses (40%), lots of fillers (5)
        res = scoring_engine.calculate_scores(
            semantic_similarity=0.30,
            keyword_coverage=0.20,
            pause_ratio=0.40,
            filler_count=5,
            duration_sec=20.0,
            word_count=16.0  # 16 / 20 * 60 = 48 WPM
        )
        
        self.assertEqual(res["understanding_level"], "Poor Understanding")
        self.assertLess(res["overall_score"], 50.0)
        self.assertTrue(any("pace is slow" in imp for imp in res["improvements"]))
        self.assertTrue(any("frequent hesitations" in imp or "pause ratio" in imp for imp in res["improvements"]))

if __name__ == '__main__':
    unittest.main()
