import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import os
import re

# Try to import LangSmith components
try:
    from langsmith import traceable
    from langsmith.client import Client
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    
    # Create dummy classes for fallback mode
    def traceable(func):
        return func
    
    class Client:
        def __init__(self, *args, **kwargs):
            pass

# Try to import pandas for data analysis
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class Observability:
    """Observability and predictive layer for LangSmith tracing, bid-timeline forecasting, and CRM integration."""

    def __init__(self, project_name: str = "QuillLeads"):
        """Initialize LangSmith tracer and observability system."""
        self.project_name = project_name
        self.logger = logging.getLogger(__name__)
        
        # Initialize LangSmith client
        self.langsmith_client = None
        self._initialize_langsmith()
        
        # Initialize fallback logging
        self.fallback_logs = []
        self._ensure_log_directory()
        
        # Statistics
        self.stats = {
            "pipeline_steps_logged": 0,
            "predictions_made": 0,
            "alerts_generated": 0,
            "crm_syncs": 0,
            "last_activity": None
        }

    def _initialize_langsmith(self):
        """Initialize LangSmith client."""
        if not LANGSMITH_AVAILABLE:
            self.logger.warning("LangSmith not available, using fallback logging")
            return
        
        try:
            # Initialize LangSmith client
            # In a real implementation, this would use actual API keys
            self.langsmith_client = Client()
            self.logger.info("LangSmith client initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize LangSmith: {e}")
            self.langsmith_client = None

    def _ensure_log_directory(self):
        """Ensure log directory exists for fallback logging."""
        try:
            log_dir = "observability_logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            self.log_file = os.path.join(log_dir, f"{self.project_name}_observability.log")
            self.logger.info(f"Fallback log directory ensured: {self.log_file}")
        except Exception as e:
            self.logger.error(f"Failed to create log directory: {e}")
            self.log_file = None

    def _fallback_log(self, data: Dict):
        """Log to file when LangSmith is not available."""
        if not self.log_file:
            return
        
        try:
            timestamp = datetime.now().isoformat()
            log_entry = {
                "timestamp": timestamp,
                "project": self.project_name,
                **data
            }
            
            # Add to memory buffer
            self.fallback_logs.append(log_entry)
            
            # Write to file
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
                
            self.logger.debug(f"Logged to fallback file: {data.get('step', 'unknown')}")
        except Exception as e:
            self.logger.error(f"Fallback logging failed: {e}")

    def _update_stats(self, metric: str, value: int = 1):
        """Update statistics."""
        if metric in self.stats:
            self.stats[metric] += value
        self.stats["last_activity"] = datetime.now().isoformat()

    @traceable
    def log_pipeline_step(self, step: str, status: str, data: dict = None, metadata: dict = None):
        """Log pipeline steps to LangSmith or fallback."""
        try:
            # Prepare log data
            log_data = {
                "step": step,
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "data": data or {},
                "metadata": metadata or {}
            }
            
            # Try LangSmith first
            if self.langsmith_client:
                try:
                    # In a real implementation, this would use LangSmith's tracing API
                    # For now, we'll simulate it by logging to the client
                    self.logger.info(f"LangSmith trace: {step} - {status}")
                    self._update_stats("pipeline_steps_logged")
                except Exception as e:
                    self.logger.error(f"LangSmith logging failed: {e}")
                    self._fallback_log(log_data)
            else:
                self._fallback_log(log_data)
                self._update_stats("pipeline_steps_logged")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Pipeline step logging failed: {e}")
            return False

    def predict_bid_timeline(self, project_data: dict) -> dict:
        """Predict project start date using simple heuristics."""
        try:
            # Extract relevant information from project data
            specs = project_data.get("project_spec", "").lower()
            description = project_data.get("description", "").lower()
            context = project_data.get("additional_context", "").lower()
            
            # Combine all text for analysis
            all_text = f"{specs} {description} {context}"
            
            # Simple heuristic-based prediction
            predicted_start = None
            confidence = 0.5
            reason = "default prediction"
            
            # Check for quarter mentions
            q3_match = re.search(r'\bq3\b|\bthird quarter\b|\bq3 \d{4}\b', all_text)
            if q3_match:
                # Predict July 1st of current year (or next year if late in current year)
                current_year = datetime.now().year
                current_month = datetime.now().month
                
                if current_month >= 7:  # Already in Q3 or later
                    predicted_start = f"{current_year + 1}-07-01"
                else:
                    predicted_start = f"{current_year}-07-01"
                
                confidence = 0.8
                reason = "Q3/third quarter mentioned in specifications"
            
            # Check for specific month mentions
            month_match = re.search(r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b', all_text)
            if month_match and not predicted_start:
                month_name = month_match.group(1)
                month_num = datetime.strptime(month_name, "%B").month
                current_year = datetime.now().year
                
                # If month is in the past, assume next year
                if datetime.now().month > month_num:
                    predicted_start = f"{current_year + 1}-{month_num:02d}-01"
                else:
                    predicted_start = f"{current_year}-{month_num:02d}-01"
                
                confidence = 0.7
                reason = f"{month_name.capitalize()} mentioned in specifications"
            
            # Check for "immediate" or "urgent" keywords
            urgent_keywords = ["immediate", "urgent", "asap", "right away", "critical"]
            if any(keyword in all_text for keyword in urgent_keywords) and not predicted_start:
                # Predict 30 days from now
                urgent_date = datetime.now() + timedelta(days=30)
                predicted_start = urgent_date.strftime("%Y-%m-%d")
                confidence = 0.6
                reason = "Urgent/immediate project mentioned"
            
            # If no specific prediction, use default (60 days from now)
            if not predicted_start:
                default_date = datetime.now() + timedelta(days=60)
                predicted_start = default_date.strftime("%Y-%m-%d")
                confidence = 0.5
                reason = "Default prediction (60 days from now)"
            
            # Log the prediction
            self.log_pipeline_step(
                "prediction",
                "success",
                {"predicted_start": predicted_start, "confidence": confidence},
                {"reason": reason, "project_data": project_data}
            )
            
            self._update_stats("predictions_made")
            
            return {
                "predicted_start": predicted_start,
                "confidence": confidence,
                "reason": reason,
                "method": "heuristic_analysis"
            }
            
        except Exception as e:
            self.logger.error(f"Bid timeline prediction failed: {e}")
            
            # Return default prediction
            default_date = datetime.now() + timedelta(days=60)
            return {
                "predicted_start": default_date.strftime("%Y-%m-%d"),
                "confidence": 0.3,
                "reason": f"Fallback prediction due to error: {str(e)}",
                "method": "fallback_default"
            }

    def _generate_alert(self, project_data: dict, lead_data: dict) -> dict:
        """Stub for predictive alerts."""
        try:
            # Get prediction
            prediction = self.predict_bid_timeline(project_data)
            predicted_start = datetime.fromisoformat(prediction["predicted_start"])
            days_until_start = (predicted_start - datetime.now()).days
            
            # Generate alert based on timeline
            alert_type = "info"
            alert_message = f"Project '{project_data.get('project_name', 'Unknown')}' predicted to start in {days_until_start} days"
            
            if days_until_start <= 30:
                alert_type = "urgent"
                alert_message = f"⚠️ URGENT: Project starts in {days_until_start} days! Immediate follow-up recommended."
            elif days_until_start <= 60:
                alert_type = "warning"
                alert_message = f"⚠️ Project starts in {days_until_start} days. Prepare follow-up."
            
            # Add lead context if available
            if lead_data:
                contact_name = f"{lead_data.get('first_name', '')} {lead_data.get('last_name', '')}".strip()
                if contact_name:
                    alert_message += f" Contact: {contact_name}"
                
                if lead_data.get("email"):
                    alert_message += f" ({lead_data['email']})"
            
            alert = {
                "alert_type": alert_type,
                "message": alert_message,
                "project_name": project_data.get("project_name", "Unknown"),
                "predicted_start": prediction["predicted_start"],
                "days_until_start": days_until_start,
                "confidence": prediction["confidence"],
                "lead_context": lead_data or {},
                "timestamp": datetime.now().isoformat()
            }
            
            self._update_stats("alerts_generated")
            return alert
            
        except Exception as e:
            self.logger.error(f"Alert generation failed: {e}")
            return {
                "alert_type": "error",
                "message": f"Failed to generate alert: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def sync_with_crm(self, lead_data: dict, crm_system: str = "salesforce") -> bool:
        """Stub for CRM sync (mock with simple-salesforce)."""
        try:
            # Validate lead data
            required_fields = ["first_name", "last_name", "email"]
            for field in required_fields:
                if field not in lead_data:
                    raise ValueError(f"Missing required field for CRM sync: {field}")
            
            # Simulate CRM sync
            sync_result = {
                "success": True,
                "crm_system": crm_system,
                "lead_id": lead_data["email"],  # Use email as ID for mock
                "timestamp": datetime.now().isoformat()
            }
            
            # Log the sync
            self.log_pipeline_step(
                "crm_sync",
                "success",
                sync_result,
                {"crm_system": crm_system, "lead_email": lead_data["email"]}
            )
            
            self._update_stats("crm_syncs")
            return True
            
        except Exception as e:
            self.logger.error(f"CRM sync failed: {e}")
            
            # Log the failure
            self.log_pipeline_step(
                "crm_sync",
                "failed",
                {"error": str(e)},
                {"crm_system": crm_system}
            )
            
            return False

    def get_observability_stats(self) -> dict:
        """Get observability statistics."""
        return {
            **self.stats,
            "langsmith_available": LANGSMITH_AVAILABLE and self.langsmith_client is not None,
            "pandas_available": PANDAS_AVAILABLE,
            "fallback_logs_count": len(self.fallback_logs),
            "log_file": self.log_file
        }

    def reset_stats(self):
        """Reset statistics."""
        self.stats = {
            "pipeline_steps_logged": 0,
            "predictions_made": 0,
            "alerts_generated": 0,
            "crm_syncs": 0,
            "last_activity": None
        }
        self.logger.info("Observability statistics reset")