import logging
import json
from typing import Dict, Any, Optional
import os

# Try to import required components
try:
    from jinja2 import Environment, FileSystemLoader, Template
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    
    # Create dummy classes for fallback mode
    class Environment:
        def __init__(self, *args, **kwargs):
            pass
    
    class FileSystemLoader:
        def __init__(self, *args, **kwargs):
            pass
    
    class Template:
        def __init__(self, *args, **kwargs):
            pass
        
        def render(self, *args, **kwargs):
            return "Fallback email template"

try:
    import yagmail
    YAGMAIL_AVAILABLE = True
except ImportError:
    YAGMAIL_AVAILABLE = False
    
    # Create dummy classes for fallback mode
    class yagmail:
        class SMTP:
            def __init__(self, *args, **kwargs):
                pass
            
            def send(self, *args, **kwargs):
                return True

from engines.orchestrator import LeadOrchestrator
from core.observability import Observability


class FinalPipeline:
    """Final pipeline integrating all agents with human-in-the-loop approval."""

    def __init__(self, orchestrator: LeadOrchestrator, observability: Observability, logger: logging.Logger = None):
        """Initialize with all agents and a logger."""
        self.orchestrator = orchestrator
        self.observability = observability
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize email components
        self.jinja_env = None
        self._initialize_jinja2()
        
        # Configuration
        self.email_config = {
            "from_email": "noreply@quilleads.com",
            "from_name": "QuillLeads Team",
            "template_dir": "email_templates",
            "smtp_user": "noreply@quilleads.com",
            "smtp_password": "password",  # In real use, this would be encrypted
            "smtp_host": "smtp.quilleads.com"
        }
        
        # Statistics
        self.stats = {
            "pipelines_run": 0,
            "emails_generated": 0,
            "emails_sent": 0,
            "approvals": 0,
            "rejections": 0,
            "last_activity": None
        }

    def _initialize_jinja2(self):
        """Initialize Jinja2 environment for email templates."""
        if not JINJA2_AVAILABLE:
            self.logger.warning("Jinja2 not available, using fallback email templates")
            return
        
        try:
            # Create templates directory if it doesn't exist
            template_dir = self.email_config["template_dir"]
            if not os.path.exists(template_dir):
                os.makedirs(template_dir)
                self.logger.info(f"Created email templates directory: {template_dir}")
            
            # Initialize Jinja2 environment
            file_system_loader = FileSystemLoader(template_dir)
            self.jinja_env = Environment(loader=file_system_loader)
            
            # Create default template if it doesn't exist
            default_template_path = os.path.join(template_dir, "default_email.txt")
            if not os.path.exists(default_template_path):
                with open(default_template_path, "w", encoding="utf-8") as f:
                    f.write(self._get_default_email_template())
                self.logger.info(f"Created default email template: {default_template_path}")
            
            self.logger.info("Jinja2 environment initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Jinja2: {e}")
            self.jinja_env = None

    def _get_default_email_template(self) -> str:
        """Return default email template content."""
        return """Subject: We hold the exact {{ part_details.name }} for your {{ project_name }}

Dear {{ contact.name }},

We have the exact {{ part_details.name }} ({{ part_details.part_number }}) in stock for your {{ project_name }} project.

{{ offer_language }}

Best regards,
{{ from_name }}
{{ from_email }}

---
QuillLeads - Rare and Vintage Computer Parts
www.quilleads.com
"""

    def _update_stats(self, metric: str, value: int = 1):
        """Update statistics."""
        if metric in self.stats:
            self.stats[metric] += value
        self.stats["last_activity"] = __import__('datetime').datetime.now().isoformat()

    def run_full_pipeline(self, project_spec: str) -> dict:
        """Run the complete pipeline with human-in-the-loop approval."""
        try:
            self.logger.info(f"Starting full pipeline for project: {project_spec[:50]}...")
            
            # Step 1: Run the orchestrator to get matched parts and contacts
            self.logger.info("Running lead orchestrator...")
            orchestrator_result = self.orchestrator.run_pipeline(project_spec)
            
            if orchestrator_result["status"] != "completed" or not orchestrator_result.get("offers"):
                error_msg = "No valid offers generated by orchestrator"
                self.logger.error(error_msg)
                self.observability.log_pipeline_step("final_pipeline", "failed", {"error": error_msg})
                return {
                    "status": "failed",
                    "error": error_msg,
                    "step": "orchestration"
                }
            
            # Step 2: Prepare lead data for the best match
            best_offer = orchestrator_result["offers"][0]  # Get the highest-scoring offer
            lead_data = self._prepare_lead_data(best_offer, project_spec, orchestrator_result)
            
            # Step 3: Generate email template
            self.logger.info("Generating email template...")
            email_subject, email_body = self.generate_email_template(lead_data)
            
            if not email_subject or not email_body:
                error_msg = "Failed to generate email template"
                self.logger.error(error_msg)
                self.observability.log_pipeline_step("email_generation", "failed", {"error": error_msg})
                return {
                    "status": "failed",
                    "error": error_msg,
                    "step": "email_generation"
                }
            
            # Add email content to lead data
            lead_data["email_subject"] = email_subject
            lead_data["email_body"] = email_body
            
            # Step 4: Log to observability
            self.observability.log_pipeline_step(
                "final_pipeline",
                "pending_approval",
                {"lead_data": lead_data},
                {"project_spec": project_spec}
            )
            
            # Step 5: Human-in-the-loop approval
            # In a real implementation, this would be a web interface or API endpoint
            # For testing, we'll use a simple input prompt
            approval = self._get_human_approval(lead_data)
            
            if approval.lower() != "approve":
                reject_reason = f"User rejected dispatch: {approval}"
                self.logger.warning(reject_reason)
                self.observability.log_pipeline_step(
                    "human_approval",
                    "rejected",
                    {"reason": approval}
                )
                self._update_stats("rejections")
                
                return {
                    "status": "rejected",
                    "reason": reject_reason,
                    "lead_data": lead_data
                }
            
            # Step 6: Send email
            self.logger.info(f"Sending email to {lead_data['contact']['email']}...")
            email_success = self.send_email(
                to=lead_data["contact"]["email"],
                subject=email_subject,
                body=email_body
            )
            
            if not email_success:
                error_msg = "Failed to send email"
                self.logger.error(error_msg)
                self.observability.log_pipeline_step("email_dispatch", "failed", {"error": error_msg})
                return {
                    "status": "failed",
                    "error": error_msg,
                    "step": "email_dispatch"
                }
            
            # Step 7: Log success and sync with CRM
            self.observability.log_pipeline_step(
                "email_dispatch",
                "success",
                {"email": lead_data["contact"]["email"], "subject": email_subject}
            )
            
            # Sync with CRM
            crm_success = self.observability.sync_with_crm(lead_data["contact"])
            if crm_success:
                self.logger.info("Successfully synced with CRM")
            else:
                self.logger.warning("CRM sync failed")
            
            # Update stats
            self._update_stats("pipelines_run")
            self._update_stats("emails_sent")
            self._update_stats("approvals")
            
            return {
                "status": "completed",
                "lead_data": lead_data,
                "email_sent": email_success,
                "crm_sync": crm_success,
                "orchestrator_result": orchestrator_result
            }
            
        except Exception as e:
            self.logger.error(f"Full pipeline execution failed: {e}")
            self.observability.log_pipeline_step("final_pipeline", "failed", {"error": str(e)})
            return {
                "status": "failed",
                "error": str(e),
                "step": "unknown"
            }

    def _prepare_lead_data(self, offer: dict, project_spec: str, orchestrator_result: dict) -> dict:
        """Prepare comprehensive lead data for email and CRM."""
        try:
            # Extract data from offer and orchestrator result
            part_details = offer["part_details"]
            
            # Create lead data structure
            lead_data = {
                "project_name": project_spec[:50],  # Truncate long project specs
                "project_spec": project_spec,
                "part_details": part_details,
                "offer_language": offer["offer_language"],
                "match_score": offer["score"],
                "contact": {
                    "name": "Valued Customer",  # Default, would be from contact harvesting in real use
                    "email": "customer@example.com",  # Default, would be from contact harvesting
                    "company": "Unknown",  # Would be from contact harvesting
                    "title": "Unknown"  # Would be from contact harvesting
                },
                "lead_source": "Parts Matching System",
                "additional_context": {
                    "orchestrator_steps": orchestrator_result["steps"],
                    "matches_found": len(orchestrator_result["matches"]),
                    "offers_generated": len(orchestrator_result["offers"])
                }
            }
            
            # If we have contact data from the orchestrator, use it
            if orchestrator_result.get("contacts"):
                contact_data = orchestrator_result["contacts"][0]
                lead_data["contact"] = {
                    "name": contact_data.get("name", "Valued Customer"),
                    "email": contact_data.get("email", "customer@example.com"),
                    "company": contact_data.get("company", "Unknown"),
                    "title": contact_data.get("title", "Unknown")
                }
            
            return lead_data
            
        except Exception as e:
            self.logger.error(f"Failed to prepare lead data: {e}")
            return {
                "project_name": project_spec[:50],
                "error": str(e)
            }

    def _get_human_approval(self, lead_data: dict) -> str:
        """Get human approval for lead dispatch."""
        try:
            # In a real implementation, this would be a web interface, API, or GUI
            # For this implementation, we'll use a simple console input
            
            # Display lead summary
            print("\n" + "="*60)
            print("LEAD DISPATCH APPROVAL REQUIRED")
            print("="*60)
            print(f"Project: {lead_data['project_name']}")
            print(f"Part: {lead_data['part_details']['name']} ({lead_data['part_details']['part_number']})")
            print(f"Contact: {lead_data['contact']['name']} <{lead_data['contact']['email']}>")
            print(f"Match Score: {lead_data['match_score']:.1%}")
            print(f"Offer: {lead_data['offer_language'][:100]}...")
            print("="*60)
            
            # Get user input
            approval = input("Approve lead dispatch? (approve/reject): ").strip().lower()
            
            if approval not in ["approve", "reject"]:
                print("Invalid input. Defaulting to reject.")
                return "reject"
            
            return approval
            
        except Exception as e:
            self.logger.error(f"Human approval failed: {e}")
            return "reject"

    def generate_email_template(self, lead_data: dict) -> tuple:
        """Generate email using Jinja2 template."""
        try:
            if not JINJA2_AVAILABLE or not self.jinja_env:
                self.logger.warning("Using fallback email template")
                return self._generate_fallback_email(lead_data)
            
            # Load the default template
            template = self.jinja_env.get_template("default_email.txt")
            
            # Prepare template context
            context = {
                "contact": lead_data["contact"],
                "part_details": lead_data["part_details"],
                "project_name": lead_data["project_name"],
                "offer_language": lead_data["offer_language"],
                "from_name": self.email_config["from_name"],
                "from_email": self.email_config["from_email"],
                "match_score": f"{lead_data['match_score']:.1%}"
            }
            
            # Render template
            rendered = template.render(context)
            
            # Parse subject and body (assuming subject is first line)
            lines = rendered.split('\n', 1)
            subject = lines[0].replace("Subject: ", "").strip()
            body = lines[1] if len(lines) > 1 else ""
            
            self._update_stats("emails_generated")
            return subject, body
            
        except Exception as e:
            self.logger.error(f"Email template generation failed: {e}")
            return self._generate_fallback_email(lead_data)

    def _generate_fallback_email(self, lead_data: dict) -> tuple:
        """Generate fallback email when Jinja2 is not available."""
        try:
            subject = f"We hold the exact {lead_data['part_details']['name']} for your project"
            body = f"""Dear {lead_data['contact']['name']},

We have the exact {lead_data['part_details']['name']} ({lead_data['part_details']['part_number']}) in stock for your project.

{lead_data['offer_language']}

Best regards,
QuillLeads Team
www.quilleads.com
"""
            
            return subject, body
            
        except Exception as e:
            self.logger.error(f"Fallback email generation failed: {e}")
            return "Parts Available for Your Project", "Please contact us regarding parts availability."

    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send email via yagmail (mock with yagmail.SMTP)."""
        try:
            if not YAGMAIL_AVAILABLE:
                self.logger.warning("Yagmail not available, simulating email send")
                self.logger.info(f"Would send email to {to}: {subject}")
                return True
            
            # In a real implementation, this would use actual SMTP credentials
            # For now, we'll simulate it
            self.logger.info(f"Simulating email send to {to}")
            self.logger.info(f"Subject: {subject}")
            self.logger.info(f"Body preview: {body[:100]}...")
            
            # Simulate successful send
            return True
            
            # Real implementation would look like:
            # yag = yagmail.SMTP(
            #     user=self.email_config["smtp_user"],
            #     password=self.email_config["smtp_password"]
            # )
            # return yag.send(
            #     to=to,
            #     subject=subject,
            #     contents=body
            # )
            
        except Exception as e:
            self.logger.error(f"Email sending failed: {e}")
            return False

    def get_pipeline_stats(self) -> dict:
        """Get pipeline statistics."""
        return {
            **self.stats,
            "jinja2_available": JINJA2_AVAILABLE,
            "yagmail_available": YAGMAIL_AVAILABLE,
            "email_config": {
                "template_dir": self.email_config["template_dir"],
                "from_email": self.email_config["from_email"]
            }
        }

    def reset_stats(self):
        """Reset statistics."""
        self.stats = {
            "pipelines_run": 0,
            "emails_generated": 0,
            "emails_sent": 0,
            "approvals": 0,
            "rejections": 0,
            "last_activity": None
        }
        self.logger.info("Pipeline statistics reset")