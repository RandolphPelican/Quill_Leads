import logging
import json
from typing import List, Dict, Optional
import os
import time
import requests
from datetime import datetime, timedelta

# Rate limiting decorator
class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period  # in seconds
        self.timestamps = []
    
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            now = time.time()
            # Remove timestamps older than period
            self.timestamps = [t for t in self.timestamps if now - t < self.period]
            
            if len(self.timestamps) >= self.calls:
                oldest = self.timestamps[0]
                wait_time = self.period - (now - oldest)
                if wait_time > 0:
                    time.sleep(wait_time)
                    # Remove the oldest timestamp after waiting
                    self.timestamps = self.timestamps[1:]
            
            # Add current timestamp
            self.timestamps.append(time.time())
            
            return func(*args, **kwargs)
        return wrapper


# Dodge Data & Analytics API client
try:
    # In a real implementation, this would use the official Dodge API client
    # For now, we'll create a custom client
    DODGE_AVAILABLE = True
except ImportError:
    DODGE_AVAILABLE = False


class DodgeAPI:
    """Dodge Data & Analytics API client."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DODGE_API_KEY")
        self.client_id = os.getenv("DODGE_CLIENT_ID")
        self.client_secret = os.getenv("DODGE_CLIENT_SECRET")
        self.base_url = "https://api.construction.com/v1"
        
        # Rate limiting: 60 calls per minute
        self.rate_limiter = RateLimiter(60, 60)
        
        # Initialize client
        self.access_token = None
        self.token_expires = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Dodge API client."""
        if not DODGE_AVAILABLE or not self.api_key:
            logging.warning("Dodge API not available or credentials not provided")
            return
        
        try:
            # In a real implementation, this would authenticate with Dodge API
            # For now, we'll simulate authentication
            self.access_token = "mock_access_token"
            self.token_expires = datetime.now() + timedelta(hours=24)
            logging.info("Dodge API client initialized")
            
        except Exception as e:
            logging.error(f"Failed to initialize Dodge API client: {e}")
            self.access_token = None
            self.token_expires = None

    @rate_limiter
    def search_projects(self, keywords: List[str], location: str = None, limit: int = 10) -> List[Dict]:
        """Search for construction projects with rate limiting."""
        if not self.access_token:
            logging.warning("Dodge API not authenticated")
            return []
        
        try:
            # In a real implementation, this would call the Dodge API
            # For now, we'll simulate it with mock data
            
            # Simulate API call delay
            time.sleep(0.2)
            
            # Mock response based on input
            results = []
            for i in range(min(3, limit)):  # Return up to 3 results
                project_type = keywords[0] if keywords else "Construction"
                results.append({
                    "id": f"dodge_{i}",
                    "name": f"{project_type} Project {i+1}",
                    "description": f"Large-scale {project_type.lower()} project in {location or 'major city'}",
                    "location": location or f"City {i+1}, State",
                    "status": "Planning" if i == 0 else "Bidding",
                    "budget": f"${(i+1)*10}M",
                    "start_date": (datetime.now() + timedelta(days=30*i)).strftime("%Y-%m-%d"),
                    "end_date": (datetime.now() + timedelta(days=365+i)).strftime("%Y-%m-%d"),
                    "project_type": project_type,
                    "source": "dodge_api",
                    "last_updated": datetime.now().isoformat()
                })
            
            return results
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Dodge API request failed: {e}")
            return []
        except Exception as e:
            logging.error(f"Dodge project search failed: {e}")
            return []


# ConstructConnect API client
try:
    # In a real implementation, this would use the official ConstructConnect API client
    CONSTRUCTCONNECT_AVAILABLE = True
except ImportError:
    CONSTRUCTCONNECT_AVAILABLE = False


class ConstructConnectAPI:
    """ConstructConnect API client."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("CONSTRUCTCONNECT_API_KEY")
        self.username = os.getenv("CONSTRUCTCONNECT_USERNAME")
        self.password = os.getenv("CONSTRUCTCONNECT_PASSWORD")
        self.base_url = "https://api.constructconnect.com/v1"
        
        # Rate limiting: 45 calls per minute
        self.rate_limiter = RateLimiter(45, 60)
        
        # Initialize client
        self.access_token = None
        self.token_expires = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ConstructConnect API client."""
        if not CONSTRUCTCONNECT_AVAILABLE or not self.api_key:
            logging.warning("ConstructConnect API not available or credentials not provided")
            return
        
        try:
            # In a real implementation, this would authenticate with ConstructConnect API
            # For now, we'll simulate authentication
            self.access_token = "mock_access_token"
            self.token_expires = datetime.now() + timedelta(hours=24)
            logging.info("ConstructConnect API client initialized")
            
        except Exception as e:
            logging.error(f"Failed to initialize ConstructConnect API client: {e}")
            self.access_token = None
            self.token_expires = None

    @rate_limiter
    def search_projects(self, keywords: List[str], location: str = None, limit: int = 10) -> List[Dict]:
        """Search for construction projects with rate limiting."""
        if not self.access_token:
            logging.warning("ConstructConnect API not authenticated")
            return []
        
        try:
            # In a real implementation, this would call the ConstructConnect API
            # For now, we'll simulate it with mock data
            
            # Simulate API call delay
            time.sleep(0.3)
            
            # Mock response based on input
            results = []
            for i in range(min(2, limit)):  # Return up to 2 results
                project_type = keywords[0] if keywords else "Infrastructure"
                results.append({
                    "id": f"cc_{i}",
                    "name": f"{project_type} Initiative {i+1}",
                    "description": f"Government-funded {project_type.lower()} initiative in {location or 'regional area'}",
                    "location": location or f"Region {i+1}",
                    "status": "Active Bidding",
                    "budget": f"${(i+2)*5}M",
                    "bid_deadline": (datetime.now() + timedelta(days=14*i)).strftime("%Y-%m-%d"),
                    "project_type": project_type,
                    "source": "constructconnect_api",
                    "contracting_method": "Design-Bid-Build",
                    "last_updated": datetime.now().isoformat()
                })
            
            return results
            
        except requests.exceptions.RequestException as e:
            logging.error(f"ConstructConnect API request failed: {e}")
            return []
        except Exception as e:
            logging.error(f"ConstructConnect project search failed: {e}")
            return []


# SAM.gov API client
try:
    # In a real implementation, this would use the official SAM.gov API client
    SAM_AVAILABLE = True
except ImportError:
    SAM_AVAILABLE = False


class SAMAPI:
    """SAM.gov API client."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("SAM_API_KEY")
        self.base_url = "https://api.sam.gov/v1"
        
        # Rate limiting: 30 calls per minute
        self.rate_limiter = RateLimiter(30, 60)
        
        # Initialize client
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize SAM.gov API client."""
        if not SAM_AVAILABLE or not self.api_key:
            logging.warning("SAM.gov API not available or API key not provided")
            return
        
        try:
            # SAM.gov uses API key authentication
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            logging.info("SAM.gov API client initialized")
            
        except Exception as e:
            logging.error(f"Failed to initialize SAM.gov API client: {e}")
            self.headers = None

    @rate_limiter
    def search_opportunities(self, keywords: List[str], naics_codes: List[str] = None, limit: int = 10) -> List[Dict]:
        """Search for government contract opportunities with rate limiting."""
        if not self.headers:
            logging.warning("SAM.gov API not authenticated")
            return []
        
        try:
            # In a real implementation, this would call the SAM.gov API
            # For now, we'll simulate it with mock data
            
            # Simulate API call delay
            time.sleep(0.5)
            
            # Mock response based on input
            results = []
            for i in range(min(2, limit)):  # Return up to 2 results
                opportunity_type = keywords[0] if keywords else "IT Services"
                naics = naics_codes[0] if naics_codes else "541511"
                
                results.append({
                    "id": f"sam_{i}",
                    "title": f"Federal {opportunity_type} Contract {i+1}",
                    "description": f"Request for proposals for {opportunity_type.lower()} services",
                    "agency": "General Services Administration",
                    "office": f"Office {i+1}",
                    "location": "Multiple Locations",
                    "status": "Open",
                    "posted_date": (datetime.now() - timedelta(days=7*i)).strftime("%Y-%m-%d"),
                    "response_deadline": (datetime.now() + timedelta(days=21*i)).strftime("%Y-%m-%d"),
                    "naics_code": naics,
                    "naics_description": "Custom Computer Programming Services",
                    "contract_value": f"${(i+1)*500}K",
                    "set_aside": "Small Business" if i == 0 else "None",
                    "source": "sam_gov_api",
                    "solicitation_number": f"GSA-{datetime.now().year}-{i+1:04d}",
                    "last_updated": datetime.now().isoformat()
                })
            
            return results
            
        except requests.exceptions.RequestException as e:
            logging.error(f"SAM.gov API request failed: {e}")
            return []
        except Exception as e:
            logging.error(f"SAM.gov opportunity search failed: {e}")
            return []


class ProjectDiscoveryAgent:
    """Project discovery agent for finding construction and government projects."""
    
    def __init__(self, logger: logging.Logger = None):
        """Initialize with a logger."""
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize API clients
        self.dodge_api = DodgeAPI()
        self.constructconnect_api = ConstructConnectAPI()
        self.sam_api = SAMAPI()
        
        # Statistics
        self.stats = {
            "dodge_searches": 0,
            "constructconnect_searches": 0,
            "sam_searches": 0,
            "projects_found": 0,
            "last_search": None
        }

    def discover_projects(self, keywords: List[str], location: str = None, naics_codes: List[str] = None) -> List[Dict]:
        """Discover projects using all available APIs."""
        all_projects = []
        
        # Search Dodge Data & Analytics
        try:
            self.logger.info(f"Searching Dodge API for projects: {', '.join(keywords)}")
            dodge_results = self.dodge_api.search_projects(keywords, location)
            if dodge_results:
                all_projects.extend(dodge_results)
                self.stats["dodge_searches"] += 1
                self.stats["projects_found"] += len(dodge_results)
                self.logger.info(f"Dodge API returned {len(dodge_results)} projects")
        except Exception as e:
            self.logger.error(f"Dodge API search failed: {e}")
        
        # Search ConstructConnect
        try:
            self.logger.info(f"Searching ConstructConnect API for projects: {', '.join(keywords)}")
            cc_results = self.constructconnect_api.search_projects(keywords, location)
            if cc_results:
                all_projects.extend(cc_results)
                self.stats["constructconnect_searches"] += 1
                self.stats["projects_found"] += len(cc_results)
                self.logger.info(f"ConstructConnect API returned {len(cc_results)} projects")
        except Exception as e:
            self.logger.error(f"ConstructConnect API search failed: {e}")
        
        # Search SAM.gov
        try:
            self.logger.info(f"Searching SAM.gov for opportunities: {', '.join(keywords)}")
            sam_results = self.sam_api.search_opportunities(keywords, naics_codes)
            if sam_results:
                all_projects.extend(sam_results)
                self.stats["sam_searches"] += 1
                self.stats["projects_found"] += len(sam_results)
                self.logger.info(f"SAM.gov API returned {len(sam_results)} opportunities")
        except Exception as e:
            self.logger.error(f"SAM.gov API search failed: {e}")
        
        # Deduplicate results
        unique_projects = self._deduplicate_projects(all_projects)
        
        # Update statistics
        self.stats["last_search"] = datetime.now().isoformat()
        
        self.logger.info(f"Discovered {len(unique_projects)} unique projects")
        return unique_projects

    def _deduplicate_projects(self, projects: List[Dict]) -> List[Dict]:
        """Deduplicate projects based on name and location."""
        seen = set()
        unique_projects = []
        
        for project in projects:
            # Create a unique identifier
            identifier = (
                project.get("name", "").lower(),
                project.get("title", "").lower(),
                project.get("location", "").lower()
            )
            
            if identifier not in seen:
                seen.add(identifier)
                unique_projects.append(project)
        
        return unique_projects

    def get_discovery_stats(self) -> Dict:
        """Get project discovery statistics."""
        return {
            **self.stats,
            "dodge_available": DODGE_AVAILABLE and self.dodge_api.access_token is not None,
            "constructconnect_available": CONSTRUCTCONNECT_AVAILABLE and self.constructconnect_api.access_token is not None,
            "sam_available": SAM_AVAILABLE and self.sam_api.headers is not None,
            "dodge_rate_limit": "60 calls/minute",
            "constructconnect_rate_limit": "45 calls/minute",
            "sam_rate_limit": "30 calls/minute"
        }

    def reset_stats(self):
        """Reset statistics."""
        self.stats = {
            "dodge_searches": 0,
            "constructconnect_searches": 0,
            "sam_searches": 0,
            "projects_found": 0,
            "last_search": None
        }
        self.logger.info("Project discovery statistics reset")