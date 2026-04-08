import logging
from typing import Dict, Any, Optional
from models.inventory_vector import InventoryVectorDB

# Try to import langgraph components
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    
    # Create dummy classes for fallback mode
    class StateGraph:
        def __init__(self, *args, **kwargs):
            pass
            
    class END:
        pass
    
    class MemorySaver:
        pass


class LeadOrchestrator:
    """Stateful StateGraph-based orchestrator for the multi-agent pipeline."""

    def __init__(self, db: InventoryVectorDB, logger: logging.Logger = None):
        """Initialize with InventoryVectorDB instance and logger."""
        self.db = db
        self.logger = logger or logging.getLogger(__name__)
        self.workflow = None
        self._initialize_workflow()

    def _initialize_workflow(self):
        """Initialize the StateGraph workflow."""
        if not LANGGRAPH_AVAILABLE:
            self.logger.warning("LangGraph not available, using linear fallback workflow")
            return
        
        # Define the workflow
        workflow = StateGraph(LeadOrchestrator.State)
        
        # Add nodes
        workflow.add_node("discover", self._discover_node)
        workflow.add_node("match", self._match_node)
        workflow.add_node("harvest", self._harvest_node)
        workflow.add_node("dispatch", self._dispatch_node)
        
        # Set entry point
        workflow.set_entry_point("discover")
        
        # Add edges
        workflow.add_edge("discover", "match")
        workflow.add_edge("match", "harvest")
        workflow.add_edge("harvest", "dispatch")
        workflow.add_edge("dispatch", END)
        
        # Add conditional edges
        def should_skip_harvest(state: self.State):
            return not state.get("matches", [])
        
        def should_skip_dispatch(state: self.State):
            return not state.get("contacts", [])
        
        workflow.add_conditional_edges(
            "match",
            should_skip_harvest,
            {
                True: "dispatch",
                False: "harvest"
            }
        )
        
        workflow.add_conditional_edges(
            "harvest",
            should_skip_dispatch,
            {
                True: END,
                False: "dispatch"
            }
        )
        
        # Compile workflow
        self.workflow = workflow.compile(checkpointer=MemorySaver())

    class State(Dict):
        """State representation for the workflow."""
        pass

    def _discover_node(self, state: State) -> State:
        """Discovery node: Query project spec against InventoryVectorDB."""
        try:
            project_spec = state.get("project_spec", "")
            if not project_spec:
                raise ValueError("No project specification provided")
            
            # Query the database
            matches = self.db.query_similar_parts(project_spec, top_k=5)
            
            self.log_transition("discovery", "success", {"matches_found": len(matches)})
            
            return {
                **state,
                "matches": matches,
                "discovery_status": "success"
            }
        except Exception as e:
            self.log_transition("discovery", "failed", {"error": str(e)})
            self.logger.error(f"Discovery failed: {e}")
            return {
                **state,
                "matches": [],
                "discovery_status": "failed",
                "discovery_error": str(e)
            }

    def _match_node(self, state: State) -> State:
        """Matching node: Score matches and generate offer language."""
        try:
            matches = state.get("matches", [])
            if not matches:
                self.log_transition("matching", "skipped", {"reason": "no_matches"})
                return {
                    **state,
                    "matching_status": "skipped",
                    "offers": []
                }
            
            # Generate offers (simple scoring for now)
            offers = []
            for i, match in enumerate(matches):
                score = 1.0 - match.get("score", 0.5)  # Convert distance to similarity
                offers.append({
                    "id": f"offer_{i}",
                    "part_id": match["id"],
                    "part_name": match["data"]["name"],
                    "score": score,
                    "offer_text": f"We have {match['data']['name']} ({match['data']['part_number']}) that matches your requirements. Score: {score:.2f}"
                })
            
            self.log_transition("matching", "success", {"offers_generated": len(offers)})
            
            return {
                **state,
                "offers": offers,
                "matching_status": "success"
            }
        except Exception as e:
            self.log_transition("matching", "failed", {"error": str(e)})
            self.logger.error(f"Matching failed: {e}")
            return {
                **state,
                "offers": [],
                "matching_status": "failed",
                "matching_error": str(e)
            }

    def _harvest_node(self, state: State) -> State:
        """Contact Harvesting node: Stub for ContactHarvester."""
        try:
            offers = state.get("offers", [])
            if not offers:
                self.log_transition("harvesting", "skipped", {"reason": "no_offers"})
                return {
                    **state,
                    "harvesting_status": "skipped",
                    "contacts": []
                }
            
            # Stub implementation - in Phase 1.3 this will use ContactHarvester
            contacts = []
            for offer in offers:
                contacts.append({
                    "offer_id": offer["id"],
                    "contact_method": "email",
                    "contact_info": "contact@example.com",  # Placeholder
                    "status": "generated"
                })
            
            self.log_transition("harvesting", "success", {"contacts_generated": len(contacts)})
            
            return {
                **state,
                "contacts": contacts,
                "harvesting_status": "success"
            }
        except Exception as e:
            self.log_transition("harvesting", "failed", {"error": str(e)})
            self.logger.error(f"Harvesting failed: {e}")
            return {
                **state,
                "contacts": [],
                "harvesting_status": "failed",
                "harvesting_error": str(e)
            }

    def _dispatch_node(self, state: State) -> State:
        """CRM Dispatch node: Stub for CRMDispatcher."""
        try:
            contacts = state.get("contacts", [])
            if not contacts:
                self.log_transition("dispatch", "skipped", {"reason": "no_contacts"})
                return {
                    **state,
                    "dispatch_status": "skipped"
                }
            
            # Stub implementation - in Phase 1.4 this will use CRMDispatcher
            dispatch_results = []
            for contact in contacts:
                dispatch_results.append({
                    "contact_id": contact["offer_id"],
                    "status": "dispatched",
                    "crm_id": f"crm_{len(dispatch_results)}",
                    "timestamp": "2024-01-01T00:00:00Z"  # Placeholder
                })
            
            self.log_transition("dispatch", "success", {"dispatches": len(dispatch_results)})
            
            return {
                **state,
                "dispatch_results": dispatch_results,
                "dispatch_status": "success"
            }
        except Exception as e:
            self.log_transition("dispatch", "failed", {"error": str(e)})
            self.logger.error(f"Dispatch failed: {e}")
            return {
                **state,
                "dispatch_results": [],
                "dispatch_status": "failed",
                "dispatch_error": str(e)
            }

    def run_pipeline(self, project_spec: str) -> dict:
        """Run the complete pipeline."""
        if not LANGGRAPH_AVAILABLE:
            return self._run_linear_pipeline(project_spec)
        
        try:
            # Initialize state
            initial_state = {
                "project_spec": project_spec,
                "matches": [],
                "offers": [],
                "contacts": [],
                "dispatch_results": []
            }
            
            # Run workflow
            final_state = self.workflow.invoke(initial_state)
            
            # Format results
            result = {
                "project_spec": project_spec,
                "matches": final_state.get("matches", []),
                "offers": final_state.get("offers", []),
                "contacts": final_state.get("contacts", []),
                "dispatch_results": final_state.get("dispatch_results", []),
                "status": "completed",
                "steps": {
                    "discovery": final_state.get("discovery_status", "not_run"),
                    "matching": final_state.get("matching_status", "not_run"),
                    "harvesting": final_state.get("harvesting_status", "not_run"),
                    "dispatch": final_state.get("dispatch_status", "not_run")
                }
            }
            
            self.log_transition("pipeline", "completed")
            return result
            
        except Exception as e:
            self.log_transition("pipeline", "failed", {"error": str(e)})
            self.logger.error(f"Pipeline execution failed: {e}")
            return {
                "project_spec": project_spec,
                "status": "failed",
                "error": str(e),
                "steps": {
                    "discovery": "failed",
                    "matching": "not_run",
                    "harvesting": "not_run",
                    "dispatch": "not_run"
                }
            }

    def _run_linear_pipeline(self, project_spec: str) -> dict:
        """Linear fallback pipeline when LangGraph is not available."""
        self.logger.warning("Running linear fallback pipeline")
        
        state = {
            "project_spec": project_spec,
            "matches": [],
            "offers": [],
            "contacts": [],
            "dispatch_results": []
        }
        
        # Run nodes sequentially
        state = self._discover_node(state)
        state = self._match_node(state)
        
        # Conditional execution
        if state.get("offers"):
            state = self._harvest_node(state)
        
        if state.get("contacts"):
            state = self._dispatch_node(state)
        
        # Format results
        result = {
            "project_spec": project_spec,
            "matches": state.get("matches", []),
            "offers": state.get("offers", []),
            "contacts": state.get("contacts", []),
            "dispatch_results": state.get("dispatch_results", []),
            "status": "completed",
            "steps": {
                "discovery": state.get("discovery_status", "not_run"),
                "matching": state.get("matching_status", "not_run"),
                "harvesting": state.get("harvesting_status", "not_run"),
                "dispatch": state.get("dispatch_status", "not_run")
            }
        }
        
        self.log_transition("pipeline", "completed")
        return result

    def log_transition(self, step: str, status: str, data: dict = None):
        """Log each transition in the pipeline."""
        log_data = {"step": step, "status": status}
        if data:
            log_data.update(data)
        
        if status == "success":
            self.logger.info(f"Step '{step}' completed successfully", extra=log_data)
        elif status == "failed":
            self.logger.error(f"Step '{step}' failed", extra=log_data)
        elif status == "skipped":
            self.logger.warning(f"Step '{step}' skipped", extra=log_data)
        else:
            self.logger.info(f"Step '{step}' transition: {status}", extra=log_data)