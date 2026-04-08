import logging
from typing import List, Dict, Optional
from models.inventory_vector import InventoryVectorDB

# Try to import LLM-related components
try:
    from sentence_transformers import SentenceTransformer
    from langchain.llms.base import LLM
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    
    # Create dummy classes for fallback mode
    class SentenceTransformer:
        def __init__(self, *args, **kwargs):
            pass
            
    class LLM:
        def __init__(self, *args, **kwargs):
            pass


class PartsMatcher:
    """Semantic parts matcher agent for scoring rare part fits and generating offer language."""

    def __init__(self, db: InventoryVectorDB, logger: logging.Logger = None):
        """Initialize with InventoryVectorDB instance and logger."""
        self.db = db
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize LLM components
        self.llm = None
        self.embedding_model = None
        self._initialize_llm()

    def _initialize_llm(self):
        """Initialize LLM and embedding components."""
        if not LLM_AVAILABLE:
            self.logger.warning("LLM components not available, using fallback mode")
            return
        
        try:
            # Initialize embedding model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.logger.info("Initialized sentence transformer model")
            
            # Initialize LLM (stub for future integration)
            # In a real implementation, this would connect to an actual LLM
            self.llm = LLM()
            self.logger.info("Initialized LLM")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM components: {e}")
            self.llm = None
            self.embedding_model = None

    def match_parts(self, project_spec: str, min_score: float = 0.7) -> List[Dict]:
        """Match parts against project specification and generate offers.
        
        Args:
            project_spec: Project specification text
            min_score: Minimum similarity score to include (0.0-1.0)
            
        Returns:
            List of matched parts with scores, details, and offer language
        """
        try:
            # Step 1: Query the database for similar parts
            self.logger.info(f"Querying database for parts matching: {project_spec[:50]}...")
            matches = self.db.query_similar_parts(project_spec, top_k=10)
            
            if not matches:
                self.logger.warning("No matches found in database")
                return []
            
            # Step 2: Score and filter matches
            scored_matches = []
            for match in matches:
                # Convert distance to similarity score (0 = perfect match, higher = worse)
                distance = match.get("score", 0.5)
                similarity_score = max(0.0, 1.0 - distance)  # Convert to 0-1 range
                
                if similarity_score >= min_score:
                    part_details = match["data"]
                    
                    # Step 3: Generate offer language
                    try:
                        offer_language = self._generate_offer_language({
                            "part_name": part_details["name"],
                            "part_number": part_details["part_number"],
                            "category": part_details["category"],
                            "project_spec": project_spec,
                            "score": similarity_score
                        })
                    except Exception as e:
                        self.logger.error(f"LLM offer generation failed: {e}")
                        offer_language = self._generate_fallback_offer_language(part_details, similarity_score)
                    
                    scored_matches.append({
                        "id": match["id"],
                        "score": similarity_score,
                        "part_details": part_details,
                        "offer_language": offer_language,
                        "source": "llm" if self.llm else "fallback"
                    })
            
            # Sort by score (highest first)
            scored_matches.sort(key=lambda x: x["score"], reverse=True)
            
            self.logger.info(f"Found {len(scored_matches)} matches above threshold {min_score}")
            return scored_matches
            
        except Exception as e:
            self.logger.error(f"Parts matching failed: {e}")
            return []

    def _generate_offer_language(self, part: Dict) -> str:
        """Generate offer language using LLM (stub with langchain for future integration)."""
        if not LLM_AVAILABLE or not self.llm:
            return self._generate_fallback_offer_language(part.get("part_details", part), part.get("score", 0.8))
        
        try:
            # In a real implementation, this would use the LLM to generate
            # personalized offer language based on the part and project spec
            
            # For now, we'll use a template that could be enhanced with LLM
            part_name = part.get("part_name", part.get("part_details", {}).get("name", "the part"))
            part_number = part.get("part_number", part.get("part_details", {}).get("part_number", ""))
            category = part.get("category", part.get("part_details", {}).get("category", "component"))
            score = part.get("score", 0.8)
            
            # Template that could be enhanced with LLM-generated content
            templates = [
                f"We hold the exact {category} you need for your project. Our {part_name} ({part_number}) is a perfect match with {score:.1%} compatibility.",
                f"Your project requirements align perfectly with our {part_name} ({part_number}) - a rare {category} with {score:.1%} match confidence.",
                f"We've identified the ideal {category} for your needs: {part_name} ({part_number}) with {score:.1%} specification alignment.",
                f"Our inventory includes the {part_name} ({part_number}) you're looking for - a {category} that matches your specs at {score:.1%}."
            ]
            
            # Select template based on score
            if score > 0.9:
                template = templates[0]  # Perfect match
            elif score > 0.8:
                template = templates[1]  # Very good match
            elif score > 0.7:
                template = templates[2]  # Good match
            else:
                template = templates[3]  # Basic match
            
            return template
            
        except Exception as e:
            self.logger.error(f"LLM offer generation failed: {e}")
            return self._generate_fallback_offer_language(part.get("part_details", part), part.get("score", 0.8))

    def _generate_fallback_offer_language(self, part_details: Dict, score: float) -> str:
        """Generate fallback offer language using hardcoded templates."""
        try:
            part_name = part_details.get("name", "the requested part")
            part_number = part_details.get("part_number", "")
            category = part_details.get("category", "component")
            
            # Fallback templates
            templates = [
                f"We have {part_name} ({part_number}) in stock - a {category} that matches your requirements.",
                f"Our inventory includes {part_name} ({part_number}), a {category} suitable for your project.",
                f"Consider {part_name} ({part_number}) for your {category} needs - we have it available.",
                f"The {part_name} ({part_number}) {category} you're looking for is in our catalog."
            ]
            
            # Select template based on score
            template_index = min(int(score * 10) % len(templates), len(templates) - 1)
            return templates[template_index]
            
        except Exception as e:
            self.logger.error(f"Fallback offer generation failed: {e}")
            return "We have a matching part available for your project requirements."

    def get_matching_stats(self) -> Dict:
        """Get matching statistics and capabilities."""
        return {
            "llm_available": LLM_AVAILABLE and self.llm is not None,
            "embedding_available": LLM_AVAILABLE and self.embedding_model is not None,
            "min_score_threshold": 0.7,
            "max_results": 10,
            "fallback_enabled": True
        }