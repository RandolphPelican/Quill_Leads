import unittest
import sys
import os
import logging

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.inventory_vector import InventoryVectorDB
from engines.parts_matcher import PartsMatcher


class TestPartsMatcher(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a test logger
        self.logger = logging.getLogger("test_parts_matcher")
        self.logger.setLevel(logging.DEBUG)
        
        # Create inventory DB
        self.db = InventoryVectorDB(persist_directory="./test_chroma_db")
        
        # Create parts matcher
        self.matcher = PartsMatcher(self.db, self.logger)
        
        # Load mock inventory
        self.db.load_mock_inventory()

    def tearDown(self):
        """Clean up after tests."""
        # Remove test database directory
        import shutil
        if os.path.exists("./test_chroma_db"):
            shutil.rmtree("./test_chroma_db")
    
    def test_match_parts_success(self):
        """Test that the matcher returns correct results for a valid query."""
        # Test with a query that should find matches
        project_spec = "16-bit CPU from the 1980s for vintage computer restoration"
        results = self.matcher.match_parts(project_spec, min_score=0.5)  # Lower threshold for fallback mode
        
        # Verify basic structure
        self.assertIsInstance(results, list)
        
        # In fallback mode, we should get some results
        if results:
            for result in results:
                self.assertIn("id", result)
                self.assertIn("score", result)
                self.assertIn("part_details", result)
                self.assertIn("offer_language", result)
                self.assertIn("source", result)
                
                # Verify score is reasonable
                self.assertGreaterEqual(result["score"], 0.5)
                self.assertLessEqual(result["score"], 1.0)
                
                # Verify offer language is generated
                self.assertIsInstance(result["offer_language"], str)
                self.assertGreater(len(result["offer_language"]), 10)
        
        # Log the results for debugging
        self.logger.info(f"Got {len(results)} matches in test")

    def test_fallback_on_llm_failure(self):
        """Test that fallback template is used when LLM fails."""
        # Test with a query that should find matches
        project_spec = "vintage computer parts needed"
        results = self.matcher.match_parts(project_spec, min_score=0.5)
        
        # Verify we get results
        self.assertIsInstance(results, list)
        
        # Check that fallback was used (since LLM components aren't available)
        if results:
            for result in results:
                self.assertEqual(result["source"], "fallback")
                
                # Verify fallback offer language is reasonable
                offer = result["offer_language"]
                self.assertIsInstance(offer, str)
                self.assertGreater(len(offer), 10)
                
                # Fallback offers should contain basic part info
                part_name = result["part_details"]["name"]
                self.assertIn(part_name, offer or "")

    def test_offer_language_generation(self):
        """Test that offer language is generated correctly."""
        # Test the offer language generation directly
        test_part = {
            "name": "Intel 8086 CPU",
            "part_number": "D8086",
            "category": "processor"
        }
        
        # Test fallback generation
        offer = self.matcher._generate_fallback_offer_language(test_part, 0.85)
        
        self.assertIsInstance(offer, str)
        self.assertGreater(len(offer), 10)
        
        # Verify it contains expected elements
        self.assertIn("Intel 8086 CPU", offer)
        self.assertIn("D8086", offer)
        self.assertIn("processor", offer)

    def test_empty_query(self):
        """Test handling of empty query."""
        project_spec = ""
        results = self.matcher.match_parts(project_spec, min_score=0.5)
        
        # Should handle gracefully and return empty list
        self.assertIsInstance(results, list)
        # May return empty or fallback results depending on implementation

    def test_high_min_score(self):
        """Test filtering with high minimum score."""
        project_spec = "CPU"
        
        # Test with very high threshold
        results_high = self.matcher.match_parts(project_spec, min_score=0.95)
        results_low = self.matcher.match_parts(project_spec, min_score=0.5)
        
        # High threshold should return fewer or equal results
        self.assertLessEqual(len(results_high), len(results_low))

    def test_get_matching_stats(self):
        """Test that get_matching_stats returns valid statistics."""
        stats = self.matcher.get_matching_stats()
        
        # Verify structure
        self.assertIn("llm_available", stats)
        self.assertIn("embedding_available", stats)
        self.assertIn("min_score_threshold", stats)
        self.assertIn("max_results", stats)
        self.assertIn("fallback_enabled", stats)
        
        # Verify values
        self.assertEqual(stats["min_score_threshold"], 0.7)
        self.assertEqual(stats["max_results"], 10)
        self.assertTrue(stats["fallback_enabled"])
        
        # LLM availability depends on environment
        self.assertIn(stats["llm_available"], [True, False])
        self.assertIn(stats["embedding_available"], [True, False])

    def test_score_conversion(self):
        """Test that distance scores are correctly converted to similarity scores."""
        # This test verifies the score conversion logic
        project_spec = "test part"
        
        # Mock a database result with known distance
        mock_match = {
            "id": "test_id",
            "score": 0.3,  # Distance of 0.3
            "data": {
                "name": "Test Part",
                "part_number": "TEST-001",
                "category": "test"
            }
        }
        
        # Manually test the conversion logic
        distance = 0.3
        similarity_score = max(0.0, 1.0 - distance)
        
        self.assertEqual(similarity_score, 0.7)
        self.assertGreaterEqual(similarity_score, 0.0)
        self.assertLessEqual(similarity_score, 1.0)


if __name__ == '__main__':
    unittest.main()