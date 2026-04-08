import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
import os
import time
import requests

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


# Real Salesforce client
try:
    from simple_salesforce import Salesforce, SalesforceMalformedRequest
    SALESFORCE_AVAILABLE = True
except ImportError:
    SALESFORCE_AVAILABLE = False
    
    class Salesforce:
        """Mock Salesforce client for fallback."""
        def __init__(self, *args, **kwargs):
            pass
        
        def Lead(self):
            return self
        
        def create(self, data):
            return {"success": False, "id": None}
    
    class SalesforceMalformedRequest(Exception):
        pass


class RealSalesforce:
    """Real Salesforce client using simple-salesforce."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.domain = config.get("domain", "login")
        self.username = config.get("username")
        self.password = config.get("password")
        self.security_token = config.get("security_token")
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        
        # Rate limiting: 100 calls per minute
        self.rate_limiter = RateLimiter(100, 60)
        
        # Initialize client
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Salesforce client."""
        if not SALESFORCE_AVAILABLE:
            self.client = None
            return
        
        try:
            # Get credentials from environment variables if not in config
            username = self.username or os.getenv("SALESFORCE_USERNAME")
            password = self.password or os.getenv("SALESFORCE_PASSWORD")
            security_token = self.security_token or os.getenv("SALESFORCE_SECURITY_TOKEN")
            client_id = self.client_id or os.getenv("SALESFORCE_CLIENT_ID")
            client_secret = self.client_secret or os.getenv("SALESFORCE_CLIENT_SECRET")
            domain = self.domain or os.getenv("SALESFORCE_DOMAIN", "login")
            
            if not all([username, password, security_token]):
                logging.warning("Salesforce credentials not provided")
                self.client = None
                return
            
            # Initialize Salesforce client
            self.client = Salesforce(
                username=username,
                password=password,
                security_token=security_token,
                client_id=client_id,
                client_secret=client_secret,
                domain=domain
            )
            
            logging.info("Salesforce client initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize Salesforce client: {e}")
            self.client = None

    @rate_limiter
    def create_lead(self, lead_data: Dict) -> Dict:
        """Create a lead in Salesforce with rate limiting."""
        if not self.client:
            logging.warning("Salesforce client not available")
            return {"success": False, "id": None, "errors": ["Client not initialized"]}
        
        try:
            # Map lead data to Salesforce fields
            sf_lead = {
                "FirstName": lead_data.get("FirstName"),
                "LastName": lead_data.get("LastName"),
                "Email": lead_data.get("Email"),
                "Phone": lead_data.get("Phone"),
                "Company": lead_data.get("Company"),
                "Title": lead_data.get("Title"),
                "Description": lead_data.get("Description"),
                "LeadSource": lead_data.get("LeadSource", "Web"),
                "Status": lead_data.get("Status", "Open - Not Contacted"),
                "Industry": lead_data.get("Industry", "Technology")
            }
            
            # Create lead
            result = self.client.Lead.create(sf_lead)
            
            if result.get("success"):
                return {
                    "success": True,
                    "id": result["id"],
                    "errors": []
                }
            else:
                return {
                    "success": False,
                    "id": None,
                    "errors": ["Failed to create lead"]
                }
            
        except SalesforceMalformedRequest as e:
            logging.error(f"Salesforce malformed request: {e}")
            return {"success": False, "id": None, "errors": [str(e)]}
        except requests.exceptions.RequestException as e:
            logging.error(f"Salesforce API request failed: {e}")
            return {"success": False, "id": None, "errors": [str(e)]}
        except Exception as e:
            logging.error(f"Salesforce lead creation failed: {e}")
            return {"success": False, "id": None, "errors": [str(e)]}


# Real HubSpot client
try:
    from hubspot import HubSpot
    from hubspot.crm.contacts import SimplePublicObjectInput
    HUBSPOT_AVAILABLE = True
except ImportError:
    HUBSPOT_AVAILABLE = False
    
    class HubSpot:
        """Mock HubSpot client for fallback."""
        def __init__(self, *args, **kwargs):
            pass
        
        def contacts(self):
            return self
        
        def basic_api(self):
            return self
        
        def create(self, data):
            return {"id": f"hs_{int(time.time())}"}


class RealHubSpot:
    """Real HubSpot client using hubspot-api-client."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.api_key = config.get("api_key") or os.getenv("HUBSPOT_API_KEY")
        
        # Rate limiting: 200 calls per minute
        self.rate_limiter = RateLimiter(200, 60)
        
        # Initialize client
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize HubSpot client."""
        if not HUBSPOT_AVAILABLE or not self.api_key:
            self.client = None
            return
        
        try:
            # Initialize HubSpot client
            self.client = HubSpot(api_key=self.api_key)
            logging.info("HubSpot client initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize HubSpot client: {e}")
            self.client = None

    @rate_limiter
    def create_contact(self, contact_data: Dict) -> Dict:
        """Create a contact in HubSpot with rate limiting."""
        if not self.client:
            logging.warning("HubSpot client not available")
            return {"id": None}
        
        try:
            # Map contact data to HubSpot properties
            properties = {
                "email": contact_data.get("email"),
                "firstname": contact_data.get("firstname"),
                "lastname": contact_data.get("lastname"),
                "phone": contact_data.get("phone"),
                "company": contact_data.get("company"),
                "jobtitle": contact_data.get("jobtitle"),
                "lifecyclestage": contact_data.get("lifecyclestage", "lead"),
                "lead_source": contact_data.get("lead_source", "WEB_FORM"),
                "description": contact_data.get("description")
            }
            
            # Create contact
            simple_public_object_input = SimplePublicObjectInput(properties=properties)
            result = self.client.crm.contacts.basic_api.create(simple_public_object_input)
            
            return {
                "id": result.id,
                "properties": result.properties,
                "createdAt": datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            logging.error(f"HubSpot API request failed: {e}")
            return {"id": None}
        except Exception as e:
            logging.error(f"HubSpot contact creation failed: {e}")
            return {"id": None}


class CRMDispatcher:
    """CRM dispatcher agent for sending matched leads to Salesforce/HubSpot."""

    def __init__(self, logger: logging.Logger = None, config: Dict = None):
        """Initialize with a logger and optional config."""
        self.logger = logger or logging.getLogger(__name__)
        self.config = config or {}
        
        # Initialize CRM clients
        self.salesforce = None
        self.hubspot = None
        
        # Statistics
        self.stats = {
            "total_dispatched": 0,
            "salesforce_success": 0,
            "hubspot_success": 0,
            "salesforce_failures": 0,
            "hubspot_failures": 0,
            "last_error": None,
            "last_dispatch_time": None
        }
        
        # API statistics
        self.api_stats = {
            "salesforce_calls": 0,
            "hubspot_calls": 0,
            "last_api_call": None
        }
        
        self._initialize_crm_clients()

    def _initialize_crm_clients(self):
        """Initialize CRM clients from config."""
        try:
            # Initialize Salesforce if config provided
            sf_config = self.config.get("salesforce", {})
            if sf_config or any([
                os.getenv("SALESFORCE_USERNAME"),
                os.getenv("SALESFORCE_PASSWORD"),
                os.getenv("SALESFORCE_SECURITY_TOKEN")
            ]):
                self.salesforce = RealSalesforce(sf_config)
                self.logger.info("Real Salesforce client initialized")
            
            # Initialize HubSpot if config provided
            hs_config = self.config.get("hubspot", {})
            if hs_config or os.getenv("HUBSPOT_API_KEY"):
                self.hubspot = RealHubSpot(hs_config)
                self.logger.info("Real HubSpot client initialized")
            
            # If no config provided, initialize with defaults (mock)
            if not self.salesforce and not self.hubspot:
                self.salesforce = MockSalesforce({
                    "domain": "login",
                    "username": "default@example.com",
                    "password": "default_password",
                    "security_token": "default_token"
                })
                self.hubspot = MockHubSpot({
                    "api_key": "default_api_key"
                })
                self.logger.info("Initialized CRM clients with default config (mock)")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize CRM clients: {e}")
            self.salesforce = None
            self.hubspot = None

    def dispatch_lead(self, lead_data: Dict) -> bool:
        """Send lead_data to Salesforce/HubSpot with fallback.
        
        Args:
            lead_data: Lead data dictionary with fields like:
                - first_name, last_name, email, phone, company, title
                - part_interest, project_description, score
                
        Returns:
            True on success, False on failure
        """
        if not lead_data:
            self.logger.error("No lead data provided")
            self._update_stats(False, "No lead data provided")
            return False
        
        # Validate lead data
        required_fields = ["first_name", "last_name", "email"]
        for field in required_fields:
            if field not in lead_data:
                error_msg = f"Missing required field: {field}"
                self.logger.error(error_msg)
                self._update_stats(False, error_msg)
                return False
        
        try:
            # Step 1: Try Salesforce first
            if self.salesforce:
                try:
                    self.logger.info(f"Attempting Salesforce dispatch for {lead_data['email']}")
                    result = self._send_to_salesforce(lead_data)
                    self.api_stats["salesforce_calls"] += 1
                    self.api_stats["last_api_call"] = datetime.now().isoformat()
                    
                    if result.get("success", False):
                        self.logger.info(f"Successfully dispatched to Salesforce: {result['id']}")
                        self._update_stats(True, None, "salesforce")
                        return True
                    else:
                        self.logger.error(f"Salesforce dispatch failed: {result.get('errors', ['Unknown error'])}")
                        self._update_stats(False, f"Salesforce error: {result.get('errors', [])}", "salesforce")
                except Exception as e:
                    self.logger.error(f"Salesforce dispatch exception: {e}")
                    self._update_stats(False, str(e), "salesforce")
            
            # Step 2: Fallback to HubSpot
            if self.hubspot:
                try:
                    self.logger.info(f"Falling back to HubSpot dispatch for {lead_data['email']}")
                    result = self._send_to_hubspot(lead_data)
                    self.api_stats["hubspot_calls"] += 1
                    self.api_stats["last_api_call"] = datetime.now().isoformat()
                    
                    if result.get("id"):
                        self.logger.info(f"Successfully dispatched to HubSpot: {result['id']}")
                        self._update_stats(True, None, "hubspot")
                        return True
                    else:
                        self.logger.error(f"HubSpot dispatch failed: No ID returned")
                        self._update_stats(False, "HubSpot: No ID returned", "hubspot")
                except Exception as e:
                    self.logger.error(f"HubSpot dispatch exception: {e}")
                    self._update_stats(False, str(e), "hubspot")
            
            # If we get here, all dispatch methods failed
            self.logger.error("All CRM dispatch methods failed")
            return False
            
        except Exception as e:
            self.logger.error(f"Dispatch failed: {e}")
            self._update_stats(False, str(e))
            return False

    def _send_to_salesforce(self, lead_data: Dict) -> Dict:
        """Send lead to Salesforce using real API."""
        try:
            # Map lead data to Salesforce fields
            sf_lead = {
                "FirstName": lead_data.get("first_name", ""),
                "LastName": lead_data.get("last_name", ""),
                "Email": lead_data.get("email", ""),
                "Phone": lead_data.get("phone", ""),
                "Company": lead_data.get("company", ""),
                "Title": lead_data.get("title", ""),
                "Description": self._format_lead_description(lead_data),
                "LeadSource": lead_data.get("lead_source", "Web"),
                "Status": "Open - Not Contacted",
                "Industry": lead_data.get("industry", "Technology")
            }
            
            # Call real Salesforce client
            result = self.salesforce.create_lead(sf_lead)
            
            # Add additional context to result
            result["crm_system"] = "salesforce"
            result["lead_email"] = lead_data["email"]
            
            return result
            
        except Exception as e:
            self.logger.error(f"Salesforce API call failed: {e}")
            return {"success": False, "errors": [str(e)], "crm_system": "salesforce"}

    def _send_to_hubspot(self, lead_data: Dict) -> Dict:
        """Send contact to HubSpot using real API."""
        try:
            # Map lead data to HubSpot fields
            hs_contact = {
                "email": lead_data.get("email", ""),
                "firstname": lead_data.get("first_name", ""),
                "lastname": lead_data.get("last_name", ""),
                "phone": lead_data.get("phone", ""),
                "company": lead_data.get("company", ""),
                "jobtitle": lead_data.get("title", ""),
                "lifecyclestage": "lead",
                "lead_source": lead_data.get("lead_source", "WEB_FORM"),
                "description": self._format_lead_description(lead_data)
            }
            
            # Call real HubSpot client
            result = self.hubspot.create_contact(hs_contact)
            
            # Add additional context to result
            result["crm_system"] = "hubspot"
            result["lead_email"] = lead_data["email"]
            
            return result
            
        except Exception as e:
            self.logger.error(f"HubSpot API call failed: {e}")
            return {"error": str(e), "crm_system": "hubspot"}

    def _format_lead_description(self, lead_data: Dict) -> str:
        """Format lead description with part and project details."""
        parts = []
        
        # Add part interest if available
        if lead_data.get("part_interest"):
            parts.append(f"Interested in: {lead_data['part_interest']}")
        
        # Add project description if available
        if lead_data.get("project_description"):
            parts.append(f"Project: {lead_data['project_description']}")
        
        # Add match score if available
        if lead_data.get("score"):
            parts.append(f"Match confidence: {lead_data['score']:.1%}")
        
        # Add any additional context
        if lead_data.get("additional_context"):
            parts.append(f"Context: {lead_data['additional_context']}")
        
        return ", ".join(parts) if parts else "Lead from parts matching system"

    def _update_stats(self, success: bool, error: str = None, system: str = None):
        """Update dispatch statistics."""
        self.stats["last_dispatch_time"] = datetime.now().isoformat()
        
        if success:
            self.stats["total_dispatched"] += 1
            if system == "salesforce":
                self.stats["salesforce_success"] += 1
            elif system == "hubspot":
                self.stats["hubspot_success"] += 1
        else:
            self.stats["last_error"] = error
            if system == "salesforce":
                self.stats["salesforce_failures"] += 1
            elif system == "hubspot":
                self.stats["hubspot_failures"] += 1

    def get_dispatch_stats(self) -> Dict:
        """Return dispatch statistics."""
        return {
            **self.stats,
            "salesforce_available": SALESFORCE_AVAILABLE and self.salesforce is not None,
            "hubspot_available": HUBSPOT_AVAILABLE and self.hubspot is not None,
            "total_crm_systems": sum(1 for c in [self.salesforce, self.hubspot] if c is not None),
            "api_calls": self.api_stats,
            "salesforce_rate_limit": "100 calls/minute",
            "hubspot_rate_limit": "200 calls/minute"
        }

    def reset_stats(self):
        """Reset statistics."""
        self.stats = {
            "total_dispatched": 0,
            "salesforce_success": 0,
            "hubspot_success": 0,
            "salesforce_failures": 0,
            "hubspot_failures": 0,
            "last_error": None,
            "last_dispatch_time": None
        }
        self.logger.info("Dispatch statistics reset")