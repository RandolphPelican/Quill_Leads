import logging
from typing import List, Dict, Optional
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Delay chromadb import to handle potential compatibility issues
chromadb = None
try:
    import chromadb
    # Test if chromadb is working properly
    from chromadb.config import Settings
    chromadb_available = True
except (ImportError, Exception) as e:
    logger.warning(f"ChromaDB not available: {e}, fallback mode will be used")
    chromadb_available = False


class InventoryVectorDB:
    """Chroma-based vector database for semantic matching of rare industrial/computer parts."""

    def __init__(self, persist_directory: str = "chroma_db"):
        """Initialize Chroma DB with local storage."""
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self._initialize_chroma()

    def _initialize_chroma(self):
        """Initialize Chroma DB client and collection."""
        global chromadb_available
        if not chromadb_available:
            logger.error("ChromaDB not available")
            self.client = None
            self.collection = None
            return
        
        try:
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            self.collection = self.client.get_or_create_collection(name="inventory")
            logger.info("Chroma DB initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Chroma DB: {e}")
            self.client = None
            self.collection = None

    def add_parts(self, parts: List[Dict]) -> bool:
        """Add parts to the vector database.
        
        Args:
            parts: List of parts, each with keys: id, part_number, name, description, specs, category.
        """
        if not self.collection:
            logger.error("Chroma collection not initialized.")
            return False
        
        try:
            ids = []
            documents = []
            metadatas = []
            
            for part in parts:
                # Combine specs and description for embedding
                combined_text = f"{part['description']} {part['specs']}"
                
                ids.append(part['id'])
                documents.append(combined_text)
                metadatas.append({
                    'part_number': part['part_number'],
                    'name': part['name'],
                    'category': part['category']
                })
            
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Added {len(parts)} parts to the database.")
            return True
        except Exception as e:
            logger.error(f"Failed to add parts: {e}")
            return False

    def query_similar_parts(self, project_spec: str, top_k: int = 5) -> List[Dict]:
        """Query similar parts based on project specification.
        
        Args:
            project_spec: Project specification text for semantic search.
            top_k: Number of top results to return.
        
        Returns:
            List of matching parts with scores and data.
        """
        if not self.collection:
            logger.error("Chroma collection not initialized.")
            return self._get_fallback_results(project_spec, top_k)
        
        try:
            results = self.collection.query(
                query_texts=[project_spec],
                n_results=top_k
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'score': results['distances'][0][i],
                    'data': {
                        'part_number': results['metadatas'][0][i]['part_number'],
                        'name': results['metadatas'][0][i]['name'],
                        'category': results['metadatas'][0][i]['category']
                    }
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return self._get_fallback_results(project_spec, top_k)

    def _get_fallback_results(self, project_spec: str, top_k: int = 5) -> List[Dict]:
        """Fallback method returning hardcoded mock results."""
        logger.warning("Using fallback results due to Chroma failure.")
        
        # Simple keyword-based fallback
        mock_results = []
        keywords = project_spec.lower().split()
        
        # Load mock inventory for fallback
        try:
            from models.mock_inventory import MOCK_INVENTORY
            for part in MOCK_INVENTORY:
                if len(mock_results) >= top_k:
                    break
                
                # Simple keyword matching
                part_text = f"{part['description']} {part['specs']}".lower()
                if any(keyword in part_text for keyword in keywords):
                    mock_results.append({
                        'id': part['id'],
                        'score': 0.5,  # Fixed fallback score
                        'data': {
                            'part_number': part['part_number'],
                            'name': part['name'],
                            'category': part['category']
                        }
                    })
        except Exception as e:
            logger.error(f"Fallback failed: {e}")
        
        return mock_results

    def migrate_to_pinecone(self, pinecone_index_name: str = None):
        """Migrate Chroma DB to Pinecone vector database."""
        try:
            # Import Pinecone client
            try:
                import pinecone
                from pinecone import Pinecone, ServerlessSpec
                PINECONE_AVAILABLE = True
            except ImportError:
                logger.error("Pinecone client not available. Install with: pip install pinecone-client")
                PINECONE_AVAILABLE = False
                return
            
            # Get Pinecone credentials from environment variables
            pinecone_api_key = os.getenv("PINECONE_API_KEY")
            pinecone_environment = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")
            index_name = pinecone_index_name or os.getenv("PINECONE_INDEX_NAME", "quilleads-inventory")
            
            if not pinecone_api_key:
                logger.error("Pinecone API key not provided. Set PINECONE_API_KEY environment variable.")
                return
            
            # Initialize Pinecone
            pinecone.init(api_key=pinecone_api_key, environment=pinecone_environment)
            
            # Check if index exists, create if not
            if index_name not in pinecone.list_indexes():
                logger.info(f"Creating Pinecone index: {index_name}")
                pinecone.create_index(
                    name=index_name,
                    metric="cosine",
                    dimension=384,  # Typical for sentence-transformers
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-west-2"
                    )
                )
                # Wait for index to be ready
                while not pinecone.describe_index(index_name).status['ready']:
                    time.sleep(1)
            
            # Connect to index
            index = pinecone.Index(index_name)
            
            # Get all data from Chroma DB
            if not self.collection:
                logger.error("Chroma collection not available for migration")
                return
            
            # Fetch all vectors from Chroma
            try:
                # Note: This is a simplified approach. In a real implementation,
                # you would need to handle pagination for large datasets
                chroma_data = self.collection.get()
                
                # Prepare data for Pinecone
                vectors = []
                for i, (id, vector) in enumerate(zip(chroma_data['ids'], chroma_data['embeddings'])):
                    metadata = chroma_data['metadatas'][i] if 'metadatas' in chroma_data else {}
                    
                    vectors.append({
                        "id": id,
                        "values": vector,
                        "metadata": metadata
                    })
                
                # Upsert data to Pinecone in batches
                batch_size = 100
                for i in range(0, len(vectors), batch_size):
                    batch = vectors[i:i + batch_size]
                    index.upsert(batch)
                    logger.info(f"Migrated batch {i//batch_size + 1}: {len(batch)} vectors")
                
                logger.info(f"Successfully migrated {len(vectors)} vectors to Pinecone index: {index_name}")
                
            except Exception as e:
                logger.error(f"Failed to fetch data from Chroma: {e}")
                return
            
        except Exception as e:
            logger.error(f"Pinecone migration failed: {e}")
            return

    def load_mock_inventory(self):
        """Load mock inventory into the database."""
        try:
            from models.mock_inventory import MOCK_INVENTORY
            # If Chroma is not available, we can still test the fallback
            if not chromadb_available:
                logger.warning("ChromaDB not available, mock inventory loaded for fallback testing")
                return True
            return self.add_parts(MOCK_INVENTORY)
        except Exception as e:
            logger.error(f"Failed to load mock inventory: {e}")
            return False