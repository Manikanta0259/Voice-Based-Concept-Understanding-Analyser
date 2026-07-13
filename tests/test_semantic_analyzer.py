import unittest
import semantic_eval

class TestSemanticAnalyzer(unittest.TestCase):

    def test_keyword_coverage_exact_match(self):
        transcript = "Cloud computing provides storage and servers over the internet."
        keywords = ["storage", "servers", "internet", "IaaS"]
        
        res = semantic_eval.evaluate_keyword_coverage(transcript, keywords)
        
        self.assertIn("storage", res["matched_keywords"])
        self.assertIn("servers", res["matched_keywords"])
        self.assertIn("internet", res["matched_keywords"])
        self.assertIn("IaaS", res["missed_keywords"])
        self.assertEqual(res["coverage_ratio"], 0.75)

    def test_keyword_coverage_singular_plural_variants(self):
        # Keyword is plural 'patterns', but transcript says singular 'pattern'
        transcript = "We try to recognize a specific pattern in the dataset."
        keywords = ["patterns"]
        
        res = semantic_eval.evaluate_keyword_coverage(transcript, keywords)
        self.assertIn("patterns", res["matched_keywords"])
        self.assertEqual(res["coverage_ratio"], 1.0)
        
        # Keyword is singular 'algorithm', but transcript says plural 'algorithms'
        transcript2 = "He used several search algorithms."
        keywords2 = ["algorithm"]
        
        res2 = semantic_eval.evaluate_keyword_coverage(transcript2, keywords2)
        self.assertIn("algorithm", res2["matched_keywords"])
        self.assertEqual(res2["coverage_ratio"], 1.0)

    def test_keyword_coverage_verb_stems(self):
        # Keyword is 'learn', transcript contains 'learning'
        transcript = "This neural network is learning to classify dogs."
        keywords = ["learn"]
        
        res = semantic_eval.evaluate_keyword_coverage(transcript, keywords)
        self.assertIn("learn", res["matched_keywords"])
        
        # Keyword is 'predict', transcript contains 'prediction'
        transcript2 = "Making accurate predictions is difficult."
        keywords2 = ["predict"]
        
        res2 = semantic_eval.evaluate_keyword_coverage(transcript2, keywords2)
        self.assertIn("predict", res2["matched_keywords"])

if __name__ == '__main__':
    unittest.main()
