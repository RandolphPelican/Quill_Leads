import spacy
from typing import List, Optional
from .base import RawLead

# Load the lightweight English model we just downloaded
nlp = spacy.load("en_core_web_sm")

class EntityExtractor:
    """
    Locally extracts Company Names (ORGs) from raw text using NLP.
    """
    def extract_companies(self, text: str) -> List[str]:
        doc = nlp(text[:5000]) # Process the first 5k chars for speed
        
        # Pull out entities labeled as 'ORG' (Organizations)
        companies = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
        
        # Remove duplicates and noise like 'Google' or 'LinkedIn' if they appear
        forbidden = {"LinkedIn", "Google", "Facebook", "Twitter", "Email", "Terms of Service"}
        unique_companies = list(set([c for c in companies if c not in forbidden]))
        
        return unique_companies

    def get_best_guess_company(self, raw_lead: RawLead) -> Optional[str]:
        companies = self.extract_companies(raw_lead.raw_content)
        
        if not companies:
            return None
            
        # Strategy: Often the first ORG mentioned in a news snippet 
        # is the subject of the article.
        return companies[0]
