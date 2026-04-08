import unittest
import sys
import os
import logging

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engines.contact_harvester import ContactHarvester


class TestContactHarvester(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a test logger
        self.logger = logging.getLogger("test_contact_harvester")
        self.logger.setLevel(logging.DEBUG)
        
        # Create contact harvester
        self.harvester = ContactHarvester(self.logger)

    def test_harvest_with_linkedin_api(self):
        """Test that contacts are harvested using LinkedIn API (mock)."""
        # Test with a company and role
        company_name = "TechCorp Inc"
        role_keywords = ["CTO", "Chief Technology Officer"]
        
        contacts = self.harvester.harvest_contacts(company_name, role_keywords)
        
        # Verify we got results
        self.assertIsInstance(contacts, list)
        self.assertGreater(len(contacts), 0, "No contacts returned")
        
        # Verify contact structure
        for contact in contacts:
            self.assertIn("id", contact)
            self.assertIn("name", contact)
            self.assertIn("title", contact)
            self.assertIn("company", contact)
            self.assertIn("email", contact)
            
        # Verify LinkedIn API was used (should get results with source=linkedin_api)
        linkedin_contacts = [c for c in contacts if c.get("source") == "linkedin_api"]
        self.assertGreater(len(linkedin_contacts), 0, "No LinkedIn API results found")
        
        # Verify API stats were tracked
        stats = self.harvester.get_stats()
        self.assertGreater(stats["api_calls"]["linkedin_calls"], 0)

    def test_fallback_to_playwright(self):
        """Test that Playwright fallback returns mock results."""
        # Test the playwright fallback method directly
        query = "Acme Corp Software Engineer"
        results = self.harvester._fallback_to_playwright(query)
        
        # Verify results
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0, "No Playwright results returned")
        
        # Verify structure
        for result in results:
            self.assertIn("id", result)
            self.assertIn("name", result)
            self.assertIn("source", result)
            self.assertEqual(result["source"], "playwright")
            self.assertIn("proxy_used", result)

    def test_fallback_to_google_dorks(self):
        """Test that Google dorks fallback returns mock results."""
        # Test the google dorks fallback method directly
        query = "Globex Corporation DevOps Engineer"
        results = self.harvester._fallback_to_google_dorks(query)
        
        # Verify results
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0, "No Google Dorks results returned")
        
        # Verify structure
        for result in results:
            self.assertIn("id", result)
            self.assertIn("name", result)
            self.assertIn("source", result)
            self.assertEqual(result["source"], "google_dorks")
            self.assertIn("dork_query", result)

    def test_fallback_chain(self):
        """Test that the complete fallback chain works."""
        # Test with a company that should trigger fallbacks
        company_name = "Obscure Company Ltd"
        role_keywords = ["Unicorn Trainer"]
        
        contacts = self.harvester.harvest_contacts(company_name, role_keywords)
        
        # Should still get some results from fallbacks
        self.assertIsInstance(contacts, list)
        self.assertGreaterEqual(len(contacts), 0)
        
        # Check that we have results from different sources
        sources = set(contact.get("source", "linkedin") for contact in contacts)
        self.assertGreaterEqual(len(sources), 1, "No results from any source")

    def test_deduplication(self):
        """Test that duplicate contacts are removed."""
        # Create test contacts with duplicates
        test_contacts = [
            {"name": "John Doe", "email": "john.doe@example.com", "id": "1"},
            {"name": "John Doe", "email": "john.doe@example.com", "id": "2"},  # Duplicate
            {"name": "Jane Smith", "email": "jane.smith@example.com", "id": "3"},
            {"name": "Bob Johnson", "email": "bob.johnson@example.com", "id": "4"},
            {"name": "Jane Smith", "email": "jane.smith@example.com", "id": "5"},  # Duplicate
        ]
        
        # Use the deduplication method
        unique_contacts = self.harvester._deduplicate_contacts(test_contacts)
        
        # Should have 3 unique contacts
        self.assertEqual(len(unique_contacts), 3)
        
        # Verify the unique contacts have different identifiers
        identifiers = set((contact["email"], contact["name"]) for contact in unique_contacts)
        self.assertEqual(len(identifiers), 3)

    def test_get_stats(self):
        """Test that get_stats returns valid statistics."""
        stats = self.harvester.get_stats()
        
        # Verify structure
        self.assertIn("linkedin_api_available", stats)
        self.assertIn("enrichment_api_available", stats)
        self.assertIn("playwright_available", stats)
        self.assertIn("google_dorks_available", stats)
        self.assertIn("max_results", stats)
        self.assertIn("timeout", stats)
        
        # Verify values
        self.assertTrue(stats["linkedin_api_available"])
        self.assertTrue(stats["enrichment_api_available"])
        self.assertTrue(stats["playwright_available"])
        self.assertTrue(stats["google_dorks_available"])
        self.assertEqual(stats["max_results"], 10)
        self.assertEqual(stats["timeout"], 30)

    def test_empty_role_keywords(self):
        """Test handling of empty role keywords."""
        company_name = "Test Company"
        role_keywords = []  # Empty list
        
        contacts = self.harvester.harvest_contacts(company_name, role_keywords)
        
        # Should still work and return results
        self.assertIsInstance(contacts, list)
        self.assertGreaterEqual(len(contacts), 0)


if __name__ == '__main__':
    unittest.main()