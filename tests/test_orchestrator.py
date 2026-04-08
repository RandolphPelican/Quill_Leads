import unittest
import sys
import os
import logging

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.inventory_vector import InventoryVectorDB
from engines.orchestrator import LeadOrchestrator


class TestLeadOrchestrator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a test logger
        self.logger = logging.getLogger("test_orchestrator")
        self.logger.setLevel(logging.DEBUG)
        
        # Create inventory DB
        self.db = InventoryVectorDB(persist_directory="./test_chroma_db")
        
        # Create orchestrator
        self.orchestrator = LeadOrchestrator(self.db, self.logger)
        
        # Load mock inventory
        self.db.load_mock_inventory()

    def tearDown(self):
        """Clean up after tests."""
        # Remove test database directory
        import shutil
        if os.path.exists("./test_chroma_db"):
            shutil.rmtree("./test_chroma_db")
    
    def test_pipeline_success(self):
        """Test that the pipeline returns correct results for a valid query."""
        # Test with a query that should find matches
        project_spec = "16-bit CPU from the 1980s"
        result = self.orchestrator.run_pipeline(project_spec)
        
        # Verify basic structure
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["project_spec"], project_spec)
        
        # Verify steps were executed
        steps = result["steps"]
        self.assertEqual(steps["discovery"], "success")
        self.assertIn(steps["matching"], ["success", "skipped"])
        
        # If we got matches, verify the full pipeline ran
        if result["matches"]:
            self.assertEqual(steps["matching"], "success")
            self.assertGreater(len(result["offers"]), 0)
            self.assertEqual(steps["harvesting"], "success")
            self.assertGreater(len(result["contacts"]), 0)
            self.assertEqual(steps["dispatch"], "success")
            self.assertGreater(len(result["dispatch_results"]), 0)
        else:
            # Fallback mode - verify we still got a valid result
            self.assertEqual(steps["matching"], "skipped")

    def test_fallback_on_failure(self):
        """Test that the pipeline skips failed steps and continues."""
        # Test with empty query to trigger discovery failure
        project_spec = ""
        result = self.orchestrator.run_pipeline(project_spec)
        
        # Verify failure was handled gracefully
        self.assertEqual(result["status"], "completed")  # Should still complete, not fail
        self.assertEqual(result["steps"]["discovery"], "failed")
        
        # Subsequent steps should be skipped or failed
        self.assertIn(result["steps"]["matching"], ["skipped", "failed"])

    def test_parallel_discovery_matching(self):
        """Test that discovery and matching can run in sequence (parallel not possible in linear fallback)."""
        # Test with a query that should find matches
        project_spec = "CPU"
        result = self.orchestrator.run_pipeline(project_spec)
        
        # Verify both discovery and matching completed
        self.assertEqual(result["steps"]["discovery"], "success")
        
        # Matching should have run if we got matches
        if result["matches"]:
            self.assertEqual(result["steps"]["matching"], "success")
            self.assertGreater(len(result["offers"]), 0)
        else:
            self.assertEqual(result["steps"]["matching"], "skipped")

    def test_conditional_edges(self):
        """Test that conditional edges work correctly."""
        # Test with a query that should find no matches
        project_spec = "nonexistent part that doesn't exist"
        result = self.orchestrator.run_pipeline(project_spec)
        
        # Discovery should succeed but find no matches
        self.assertEqual(result["steps"]["discovery"], "success")
        self.assertEqual(len(result["matches"]), 0)
        
        # Matching should be skipped due to no matches
        self.assertEqual(result["steps"]["matching"], "skipped")
        
        # Harvest and dispatch should also be skipped or not run
        self.assertIn(result["steps"]["harvesting"], ["skipped", "not_run"])
        self.assertIn(result["steps"]["dispatch"], ["skipped", "not_run"])

    def test_log_transition(self):
        """Test that transitions are logged correctly."""
        # This test verifies that the log_transition method works
        # We'll check that it doesn't throw errors
        try:
            self.orchestrator.log_transition("test_step", "success", {"test": "data"})
            self.orchestrator.log_transition("test_step", "failed", {"error": "test error"})
            self.orchestrator.log_transition("test_step", "skipped", {"reason": "test"})
            
            # If we get here, the method works
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"log_transition method failed: {e}")


if __name__ == '__main__':
    unittest.main()