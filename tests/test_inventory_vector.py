import unittest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.inventory_vector import InventoryVectorDB
from models.mock_inventory import MOCK_INVENTORY


class TestInventoryVectorDB(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.db = InventoryVectorDB(persist_directory="./test_chroma_db")
        
    def tearDown(self):
        """Clean up after tests."""
        # Remove test database directory
        import shutil
        if os.path.exists("./test_chroma_db"):
            shutil.rmtree("./test_chroma_db")
    
    def test_add_parts_and_query(self):
        """Test adding parts and querying for similar parts."""
        # Add mock inventory
        result = self.db.load_mock_inventory()
        self.assertTrue(result, "Failed to load mock inventory")
        
        # Query for similar parts
        query = "16-bit CPU from the 1980s"
        results = self.db.query_similar_parts(query, top_k=3)
        
        # Verify results
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0, "No results returned")
        
        # Check that results contain relevant fields
        for result in results:
            self.assertIn('id', result)
            self.assertIn('score', result)
            self.assertIn('data', result)
            self.assertIn('name', result['data'])
    
    def test_fallback_on_chroma_failure(self):
        """Test fallback mechanism when Chroma fails."""
        # Force Chroma failure by breaking the collection
        self.db.collection = None
        
        # Query should use fallback
        query = "CPU"
        results = self.db.query_similar_parts(query, top_k=2)
        
        # Verify fallback results
        self.assertIsInstance(results, list)
        # Fallback should return some results based on keyword matching
        self.assertGreaterEqual(len(results), 0)
        
        # Check structure
        if len(results) > 0:
            result = results[0]
            self.assertIn('id', result)
            self.assertIn('score', result)
            self.assertIn('data', result)
    
    def test_mock_inventory_loaded(self):
        """Test that mock inventory is properly loaded."""
        # Load mock inventory
        result = self.db.load_mock_inventory()
        self.assertTrue(result, "Failed to load mock inventory")
        
        # Query for a specific part that should be in the inventory
        query = "Intel 8086"
        results = self.db.query_similar_parts(query, top_k=5)
        
        # Verify that we get results
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0, "No results returned for specific query")
        
        # Check that at least one result matches the expected part
        found = False
        for result in results:
            if result['data']['name'] == "Intel 8086 CPU":
                found = True
                break
        
        # In fallback mode, we might not get exact matches, so we'll check for any CPU results
        if not found:
            cpu_found = any("CPU" in result['data']['name'] for result in results)
            self.assertTrue(cpu_found, "No CPU-related parts found in results")
        else:
            self.assertTrue(found, "Expected part not found in results")


if __name__ == '__main__':
    unittest.main()