import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

# Mock CRM clients
class MockSalesforce:
    """Mock Salesforce client using simple-salesforce interface."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.domain = config.get("domain", "login")
        self.username = config.get("username", "test@example.com")
        self.connected = True
        self.lead_count = 0
    
    def create_lead(self, lead_data: Dict) -> Dict:
        """Mock Salesforce lead creation."""
        if not self.connected:
            raise Exception("Not connected to Salesforce")
        
        # Simulate successful creation
        self.lead_count += 1
        return {
            "success": True,
            "id": f"sf_{self.lead_count}",
            "errors": []
        }
    
    def disconnect(self):
        """Disconnect from Salesforce."""
        self.connected = False


class MockHubSpot:
    """Mock HubSpot client using requests interface."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.api_key = config.get("api_key", "mock_api_key")
        self.lead_count = 0
    
    def create_contact(self, contact_data: Dict) -> Dict:
        """Mock HubSpot contact creation."""
        # Simulate successful creation
        self.lead_count += 1
        return {
            "id": f"hs_{self.lead_count}",
            "properties": contact_data,
            "createdAt": datetime.now().isoformat()
        }


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
        
        self._initialize_crm_clients()

    def _initialize_crm_clients(self):
        """Initialize CRM clients from config."""
        try:
            # Initialize Salesforce if config provided
            sf_config = self.config.get("salesforce", {})
            if sf_config:
                self.salesforce = MockSalesforce(sf_config)
                self.logger.info("Salesforce client initialized")
            
            # Initialize HubSpot if config provided
            hs_config = self.config.get("hubspot", {})
            if hs_config:
                self.hubspot = MockHubSpot(hs_config)
                self.logger.info("HubSpot client initialized")
            
            # If no config provided, initialize with defaults
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
                self.logger.info("Initialized CRM clients with default config")
                
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
        """Stub for Salesforce API call using simple-salesforce."""
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
            
            # Call mock Salesforce client
            result = self.salesforce.create_lead(sf_lead)
            
            # Add additional context to result
            result["crm_system"] = "salesforce"
            result["lead_email"] = lead_data["email"]
            
            return result
            
        except Exception as e:
            self.logger.error(f"Salesforce API call failed: {e}")
            return {"success": False, "errors": [str(e)], "crm_system": "salesforce"}

    def _send_to_hubspot(self, lead_data: Dict) -> Dict:
        """Stub for HubSpot API call using requests."""
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
            
            # Call mock HubSpot client
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
            "salesforce_available": self.salesforce is not None,
            "hubspot_available": self.hubspot is not None,
            "total_crm_systems": sum(1 for c in [self.salesforce, self.hubspot] if c is not None)
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