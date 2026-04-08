import unittest
import sys
import os
import logging

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engines.project_discovery import ProjectDiscoveryAgent


class TestProjectDiscovery(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a test logger
        self.logger = logging.getLogger("test_project_discovery")
        self.logger.setLevel(logging.DEBUG)
        
        # Create project discovery agent
        self.discovery_agent = ProjectDiscoveryAgent(self.logger)

    def test_discover_projects(self):
        """Test that projects are discovered from all APIs."""
        # Test with construction keywords
        keywords = ["hospital", "construction"]
        location = "New York"
        
        projects = self.discovery_agent.discover_projects(keywords, location)
        
        # Verify we got results
        self.assertIsInstance(projects, list)
        self.assertGreater(len(projects), 0, "No projects returned")
        
        # Verify project structure
        for project in projects:
            self.assertIn("id", project)
            self.assertIn("name", project)
            self.assertIn("description", project)
            self.assertIn("source", project)
        
        # Verify we got results from multiple sources
        sources = set(project["source"] for project in projects)
        self.assertGreaterEqual(len(sources), 1, "No results from any source")
        
        # Verify stats were updated
        stats = self.discovery_agent.get_discovery_stats()
        self.assertGreater(stats["projects_found"], 0)

    def test_discover_projects_with_naics(self):
        """Test project discovery with NAICS codes."""
        # Test with government contract keywords and NAICS codes
        keywords = ["IT services", "software development"]
        naics_codes = ["541511", "541512"]
        
        projects = self.discovery_agent.discover_projects(keywords, naics_codes=naics_codes)
        
        # Verify we got results
        self.assertIsInstance(projects, list)
        
        # Should get SAM.gov results
        sam_projects = [p for p in projects if p.get("source") == "sam_gov_api"]
        self.assertGreaterEqual(len(sam_projects), 0, "No SAM.gov results found")

    def test_get_discovery_stats(self):
        """Test that get_discovery_stats returns valid statistics."""
        stats = self.discovery_agent.get_discovery_stats()
        
        # Verify structure
        self.assertIn("dodge_searches", stats)
        self.assertIn("constructconnect_searches", stats)
        self.assertIn("sam_searches", stats)
        self.assertIn("projects_found", stats)
        self.assertIn("last_search", stats)
        self.assertIn("dodge_available", stats)
        self.assertIn("constructconnect_available", stats)
        self.assertIn("sam_available", stats)
        
        # Verify initial values
        self.assertEqual(stats["dodge_searches"], 0)
        self.assertEqual(stats["constructconnect_searches"], 0)
        self.assertEqual(stats["sam_searches"], 0)
        self.assertEqual(stats["projects_found"], 0)
        self.assertIsNone(stats["last_search"])

    def test_reset_stats(self):
        """Test that reset_stats works correctly."""
        # First, run a discovery to have some stats
        self.discovery_agent.discover_projects(["test"], "test location")
        
        # Verify stats are not zero
        stats_before = self.discovery_agent.get_discovery_stats()
        self.assertGreater(stats_before["dodge_searches"], 0)
        
        # Reset stats
        self.discovery_agent.reset_stats()
        
        # Verify stats are reset
        stats_after = self.discovery_agent.get_discovery_stats()
        self.assertEqual(stats_after["dodge_searches"], 0)
        self.assertEqual(stats_after["constructconnect_searches"], 0)
        self.assertEqual(stats_after["sam_searches"], 0)
        self.assertEqual(stats_after["projects_found"], 0)
        self.assertIsNone(stats_after["last_search"])

    def test_project_deduplication(self):
        """Test that duplicate projects are removed."""
        # Create test projects with duplicates
        test_projects = [
            {
                "id": "1",
                "name": "Hospital Construction",
                "description": "New hospital building",
                "location": "New York, NY",
                "source": "dodge_api"
            },
            {
                "id": "2",
                "name": "Hospital Construction",
                "description": "New hospital building",
                "location": "New York, NY",
                "source": "constructconnect_api"
            },
            {
                "id": "3",
                "name": "Bridge Repair",
                "description": "Bridge maintenance project",
                "location": "Boston, MA",
                "source": "dodge_api"
            }
        ]
        
        # Use the internal deduplication method
        unique_projects = self.discovery_agent._deduplicate_projects(test_projects)
        
        # Should have 2 unique projects (Hospital Construction and Bridge Repair)
        self.assertEqual(len(unique_projects), 2)
        
        # Verify the unique projects have different identifiers
        identifiers = set(
            (p["name"].lower(), p["location"].lower()) 
            for p in unique_projects
        )
        self.assertEqual(len(identifiers), 2)

    def test_api_availability_stats(self):
        """Test that API availability is reported correctly."""
        stats = self.discovery_agent.get_discovery_stats()
        
        # Verify API availability flags
        self.assertIn("dodge_available", stats)
        self.assertIn("constructconnect_available", stats)
        self.assertIn("sam_available", stats)
        
        # Verify rate limit information
        self.assertIn("dodge_rate_limit", stats)
        self.assertIn("constructconnect_rate_limit", stats)
        self.assertIn("sam_rate_limit", stats)


if __name__ == '__main__':
    unittest.main()