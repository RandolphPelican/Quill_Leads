import unittest
import sys
import os
import logging

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engines.crm_dispatcher import CRMDispatcher


class TestCRMDispatcher(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a test logger
        self.logger = logging.getLogger("test_crm_dispatcher")
        self.logger.setLevel(logging.DEBUG)
        
        # Create CRM dispatcher with default config
        self.dispatcher = CRMDispatcher(self.logger)

    def test_dispatch_to_salesforce(self):
        """Test that dispatch to Salesforce succeeds (mock response)."""
        # Create test lead data
        lead_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567",
            "company": "TechCorp Inc",
            "title": "CTO",
            "part_interest": "Intel 8086 CPU",
            "project_description": "Vintage computer restoration",
            "score": 0.95,
            "lead_source": "Web Form"
        }
        
        # Dispatch the lead
        result = self.dispatcher.dispatch_lead(lead_data)
        
        # Verify success
        self.assertTrue(result, "Salesforce dispatch should succeed")
        
        # Verify stats were updated
        stats = self.dispatcher.get_dispatch_stats()
        self.assertEqual(stats["total_dispatched"], 1)
        self.assertEqual(stats["salesforce_success"], 1)
        self.assertEqual(stats["hubspot_success"], 0)

    def test_fallback_to_hubspot(self):
        """Test that fallback to HubSpot works when Salesforce fails."""
        # Disconnect Salesforce to force fallback
        if self.dispatcher.salesforce:
            self.dispatcher.salesforce.disconnect()
        
        # Create test lead data
        lead_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",
            "phone": "+1-555-987-6543",
            "company": "Acme Corp",
            "title": "Engineering Manager",
            "part_interest": "VGA Graphics Card",
            "project_description": "Retro gaming PC build",
            "score": 0.87,
            "lead_source": "Email Campaign"
        }
        
        # Dispatch the lead
        result = self.dispatcher.dispatch_lead(lead_data)
        
        # Verify success (should fallback to HubSpot)
        self.assertTrue(result, "HubSpot fallback should succeed")
        
        # Verify stats were updated
        stats = self.dispatcher.get_dispatch_stats()
        self.assertEqual(stats["total_dispatched"], 1)
        self.assertEqual(stats["salesforce_success"], 0)
        self.assertEqual(stats["hubspot_success"], 1)
        self.assertGreater(stats["salesforce_failures"], 0)

    def test_get_dispatch_stats(self):
        """Test that get_dispatch_stats returns valid statistics."""
        stats = self.dispatcher.get_dispatch_stats()
        
        # Verify structure
        self.assertIn("total_dispatched", stats)
        self.assertIn("salesforce_success", stats)
        self.assertIn("hubspot_success", stats)
        self.assertIn("salesforce_failures", stats)
        self.assertIn("hubspot_failures", stats)
        self.assertIn("last_error", stats)
        self.assertIn("last_dispatch_time", stats)
        self.assertIn("salesforce_available", stats)
        self.assertIn("hubspot_available", stats)
        self.assertIn("total_crm_systems", stats)
        
        # Verify initial values
        self.assertEqual(stats["total_dispatched"], 0)
        self.assertEqual(stats["salesforce_success"], 0)
        self.assertEqual(stats["hubspot_success"], 0)
        self.assertEqual(stats["salesforce_failures"], 0)
        self.assertEqual(stats["hubspot_failures"], 0)
        self.assertIsNone(stats["last_error"])
        self.assertIsNone(stats["last_dispatch_time"])
        self.assertTrue(stats["salesforce_available"])
        self.assertTrue(stats["hubspot_available"])
        self.assertEqual(stats["total_crm_systems"], 2)

    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        # Test with missing email
        lead_data = {
            "first_name": "Bob",
            "last_name": "Johnson",
            # Missing email
            "phone": "+1-555-555-5555"
        }
        
        result = self.dispatcher.dispatch_lead(lead_data)
        
        # Should fail
        self.assertFalse(result, "Should fail with missing required fields")
        
        # Verify error was logged in stats
        stats = self.dispatcher.get_dispatch_stats()
        self.assertIsNotNone(stats["last_error"])
        self.assertIn("email", stats["last_error"].lower())

    def test_empty_lead_data(self):
        """Test handling of empty lead data."""
        result = self.dispatcher.dispatch_lead({})
        
        # Should fail
        self.assertFalse(result, "Should fail with empty lead data")
        
        # Verify error was logged
        stats = self.dispatcher.get_dispatch_stats()
        self.assertIsNotNone(stats["last_error"])
        self.assertIn("no lead data", stats["last_error"].lower())

    def test_lead_description_formatting(self):
        """Test that lead description is formatted correctly."""
        # Create test lead data
        lead_data = {
            "first_name": "Alice",
            "last_name": "Williams",
            "email": "alice.williams@example.com",
            "company": "Globex Corp",
            "title": "Hardware Engineer",
            "part_interest": "Seagate ST225 Hard Drive",
            "project_description": "IBM PC XT restoration",
            "score": 0.92,
            "additional_context": "Urgent project, needs parts ASAP"
        }
        
        # Use the internal method to format description
        description = self.dispatcher._format_lead_description(lead_data)
        
        # Verify description contains expected elements
        self.assertIn("Seagate ST225 Hard Drive", description)
        self.assertIn("IBM PC XT restoration", description)
        self.assertIn("92.0%", description)
        self.assertIn("Urgent project", description)

    def test_multiple_dispatches(self):
        """Test multiple dispatches and stats tracking."""
        # Reset stats first
        self.dispatcher.reset_stats()
        
        # Create multiple test leads
        leads = [
            {
                "first_name": "Lead",
                "last_name": f"{i}",
                "email": f"lead{i}@example.com",
                "company": f"Company {i}",
                "title": "Engineer",
                "part_interest": f"Part {i}",
                "project_description": f"Project {i}",
                "score": 0.8 + i * 0.05
            }
            for i in range(3)
        ]
        
        # Dispatch all leads
        results = []
        for lead in leads:
            result = self.dispatcher.dispatch_lead(lead)
            results.append(result)
        
        # All should succeed
        self.assertEqual(sum(results), len(results), "All dispatches should succeed")
        
        # Verify stats
        stats = self.dispatcher.get_dispatch_stats()
        self.assertEqual(stats["total_dispatched"], 3)
        self.assertEqual(stats["salesforce_success"], 3)
        self.assertEqual(stats["hubspot_success"], 0)

    def test_reset_stats(self):
        """Test that reset_stats works correctly."""
        # First, dispatch a lead to have some stats
        lead_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test.user@example.com",
            "company": "Test Corp",
            "title": "Test Engineer"
        }
        self.dispatcher.dispatch_lead(lead_data)
        
        # Verify stats are not zero
        stats_before = self.dispatcher.get_dispatch_stats()
        self.assertGreater(stats_before["total_dispatched"], 0)
        
        # Reset stats
        self.dispatcher.reset_stats()
        
        # Verify stats are reset
        stats_after = self.dispatcher.get_dispatch_stats()
        self.assertEqual(stats_after["total_dispatched"], 0)
        self.assertEqual(stats_after["salesforce_success"], 0)
        self.assertEqual(stats_after["hubspot_success"], 0)
        self.assertEqual(stats_after["salesforce_failures"], 0)
        self.assertEqual(stats_after["hubspot_failures"], 0)
        self.assertIsNone(stats_after["last_error"])
        self.assertIsNone(stats_after["last_dispatch_time"])


if __name__ == '__main__':
    unittest.main()