import logging
import json
from typing import List, Dict, Optional
import os

# Mock external API clients
class MockLinkedInAPI:
    """Mock LinkedIn Sales Navigator API client."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("LINKEDIN_API_KEY", "mock_api_key")
        self.base_url = "https://api.linkedin.com/v2"
    
    def search_people(self, company_name: str, role_keywords: List[str], limit: int = 10) -> List[Dict]:
        """Mock LinkedIn people search."""
        # Simulate API response
        results = []
        for i in range(min(3, limit)):  # Return 3 mock results
            results.append({
                "id": f"linkedin_{i}",
                "name": f"John Doe {i}",
                "title": f"Senior {role_keywords[0] if role_keywords else 'Engineer'}",
                "company": company_name,
                "linkedin_url": f"https://linkedin.com/in/johndoe{i}",
                "connection_degree": 2,
                "profile_picture": f"https://linkedin.com/pic/{i}",
                "location": "San Francisco, CA"
            })
        return results


class MockEnrichmentAPI:
    """Mock enrichment API (SociaVault-style)."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ENRICHMENT_API_KEY", "mock_enrichment_key")
        self.base_url = "https://api.enrichment.com/v1"
    
    def validate_and_enrich(self, profiles: List[Dict]) -> List[Dict]:
        """Mock profile validation and enrichment."""
        enriched = []
        for profile in profiles:
            enriched.append({
                **profile,
                "email": f"{profile['name'].replace(' ', '.').lower()}@example.com",
                "phone": "+1-555-123-4567",
                "verified": True,
                "seniority": "senior",
                "department": "engineering",
                "company_size": "1001-5000",
                "industry": "technology"
            })
        return enriched


class ContactHarvester:
    """Modular contact harvester with 2026-compliant fallback chain."""

    def __init__(self, logger: logging.Logger = None):
        """Initialize with a logger."""
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize API clients
        self.linkedin_api = MockLinkedInAPI()
        self.enrichment_api = MockEnrichmentAPI()
        
        # Configuration
        self.max_results = 10
        self.timeout = 30

    def harvest_contacts(self, company_name: str, role_keywords: List[str]) -> List[Dict]:
        """Harvest contacts using the fallback chain.
        
        Fallback chain:
        1. LinkedIn Sales Navigator API
        2. Enrichment API for validation
        3. Playwright + Residential Proxies (stub)
        4. Google Dorks (stub)
        
        Args:
            company_name: Target company name
            role_keywords: List of role keywords to search for
            
        Returns:
            List of contact dictionaries with verified information
        """
        contacts = []
        
        # Step 1: Try LinkedIn Sales Navigator API
        try:
            self.logger.info(f"Attempting LinkedIn API search for {company_name}")
            linkedin_results = self.linkedin_api.search_people(company_name, role_keywords, self.max_results)
            
            if linkedin_results:
                self.logger.info(f"LinkedIn API returned {len(linkedin_results)} results")
                
                # Step 2: Validate and enrich with enrichment API
                try:
                    enriched_contacts = self.enrichment_api.validate_and_enrich(linkedin_results)
                    contacts.extend(enriched_contacts)
                    self.logger.info(f"Enrichment API validated {len(enriched_contacts)} contacts")
                    
                    # If we have good results, return them
                    if len(contacts) >= 3:
                        self.logger.info("Sufficient contacts found, skipping fallbacks")
                        return contacts
                    
                except Exception as e:
                    self.logger.error(f"Enrichment API failed: {e}")
                    # Continue with unenriched results
                    contacts.extend(linkedin_results)
        
        except Exception as e:
            self.logger.error(f"LinkedIn API failed: {e}")
        
        # Step 3: Fallback to Playwright + Residential Proxies
        if len(contacts) < 3:  # Only use fallback if we don't have enough contacts
            try:
                self.logger.info("Falling back to Playwright scraping")
                playwright_results = self._fallback_to_playwright(f"{company_name} {' '.join(role_keywords)}")
                
                if playwright_results:
                    contacts.extend(playwright_results)
                    self.logger.info(f"Playwright returned {len(playwright_results)} results")
                    
                    # If we now have enough, return
                    if len(contacts) >= 3:
                        return contacts
                
            except Exception as e:
                self.logger.error(f"Playwright fallback failed: {e}")
        
        # Step 4: Final fallback to Google Dorks
        if len(contacts) < 3:
            try:
                self.logger.info("Falling back to Google Dorks")
                dorks_results = self._fallback_to_google_dorks(f"{company_name} {' '.join(role_keywords)}")
                
                if dorks_results:
                    contacts.extend(dorks_results)
                    self.logger.info(f"Google Dorks returned {len(dorks_results)} results")
                
            except Exception as e:
                self.logger.error(f"Google Dorks fallback failed: {e}")
        
        # Deduplicate results
        unique_contacts = self._deduplicate_contacts(contacts)
        
        self.logger.info(f"Contact harvesting completed with {len(unique_contacts)} unique contacts")
        return unique_contacts

    def _fallback_to_playwright(self, query: str) -> List[Dict]:
        """Stub for Playwright-based scraping with residential proxies."""
        self.logger.info(f"Playwright stub: would scrape for '{query}' with BrightData/Oxylabs proxies")
        
        # Mock results
        results = []
        for i in range(2):  # Return 2 mock results
            results.append({
                "id": f"playwright_{i}",
                "name": f"Playwright User {i}",
                "title": "Software Engineer",
                "company": query.split()[0],  # Extract company from query
                "source": "playwright",
                "url": f"https://example.com/profile{i}",
                "email": f"playwright{i}@example.com",
                "phone": "+1-555-987-6543",
                "verified": False,  # Playwright results are not pre-verified
                "proxy_used": "brightdata_residential"
            })
        
        return results

    def _fallback_to_google_dorks(self, query: str) -> List[Dict]:
        """Stub for Google dorks scraping."""
        self.logger.info(f"Google Dorks stub: would search with dorks for '{query}'")
        
        # Mock results
        results = []
        for i in range(1):  # Return 1 mock result
            results.append({
                "id": f"dorks_{i}",
                "name": f"Dorks User {i}",
                "title": "Engineering Manager",
                "company": query.split()[0],  # Extract company from query
                "source": "google_dorks",
                "url": f"https://docs.example.com/user{i}",
                "email": f"dorks{i}@example.com",
                "phone": None,
                "verified": False,  # Dorks results are not verified
                "dork_query": f'site:linkedin.com inurl:in "{query}"'
            })
        
        return results

    def _deduplicate_contacts(self, contacts: List[Dict]) -> List[Dict]:
        """Deduplicate contacts based on email and name."""
        seen = set()
        unique_contacts = []
        
        for contact in contacts:
            # Create a unique identifier
            identifier = (contact.get("email", ""), contact.get("name", ""))
            
            if identifier not in seen:
                seen.add(identifier)
                unique_contacts.append(contact)
        
        return unique_contacts

    def get_stats(self) -> Dict:
        """Get harvesting statistics."""
        return {
            "linkedin_api_available": True,
            "enrichment_api_available": True,
            "playwright_available": True,  # Stub
            "google_dorks_available": True,  # Stub
            "max_results": self.max_results,
            "timeout": self.timeout
        }