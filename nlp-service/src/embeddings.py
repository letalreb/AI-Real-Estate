"""
Embedding generation and vector storage.
Uses sentence-transformers or OpenAI for embeddings.
"""
import os
from typing import List, Optional, Dict, Any
import structlog
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import hashlib

logger = structlog.get_logger()

# Initialize embedding model
EMBEDDING_PROVIDER = os.getenv('EMBEDDING_PROVIDER', 'sentence-transformers')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'paraphrase-multilingual-MiniLM-L12-v2')
EMBEDDING_DIMENSION = int(os.getenv('EMBEDDING_DIMENSION', '384'))

if EMBEDDING_PROVIDER == 'sentence-transformers':
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("loaded_sentence_transformer", model=EMBEDDING_MODEL)
    except ImportError:
        logger.error("sentence_transformers_not_installed")
        model = None
elif EMBEDDING_PROVIDER == 'openai':
    try:
        import openai
        openai.api_key = os.getenv('OPENAI_API_KEY')
        model = 'openai'
        logger.info("configured_openai_embeddings")
    except ImportError:
        logger.error("openai_not_installed")
        model = None
else:
    model = None
    logger.warning("no_embedding_provider")

# Initialize Qdrant client
QDRANT_URL = os.getenv('QDRANT_URL', 'http://qdrant:6333')
QDRANT_COLLECTION = os.getenv('QDRANT_COLLECTION', 'auctions')

try:
    qdrant_client = QdrantClient(url=QDRANT_URL)
    
    # Create collection if it doesn't exist
    try:
        qdrant_client.get_collection(QDRANT_COLLECTION)
    except Exception:
        qdrant_client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=EMBEDDING_DIMENSION,
                distance=Distance.COSINE
            )
        )
        logger.info("created_qdrant_collection", collection=QDRANT_COLLECTION)
except Exception as e:
    logger.error("qdrant_connection_failed", error=str(e))
    qdrant_client = None


def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding vector for text.
    
    Args:
        text: Input text
    
    Returns:
        Embedding vector
    """
    if not text or not model:
        # Return zero vector if no model
        return [0.0] * EMBEDDING_DIMENSION
    
    try:
        if EMBEDDING_PROVIDER == 'sentence-transformers':
            embedding = model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        
        elif EMBEDDING_PROVIDER == 'openai':
            import openai
            response = openai.Embedding.create(
                input=text,
                model=EMBEDDING_MODEL
            )
            return response['data'][0]['embedding']
    
    except Exception as e:
        logger.error("embedding_generation_failed", error=str(e))
        return [0.0] * EMBEDDING_DIMENSION


async def store_in_qdrant(
    auction_id: str,
    embedding: List[float],
    metadata: Dict[str, Any]
) -> Optional[str]:
    """
    Store embedding in Qdrant vector database.
    
    Args:
        auction_id: Unique auction identifier
        embedding: Embedding vector
        metadata: Auction metadata
    
    Returns:
        Point ID in Qdrant
    """
    if not qdrant_client:
        logger.warning("qdrant_client_not_available")
        return None
    
    try:
        # Generate deterministic point ID from auction_id
        point_id = int(hashlib.md5(auction_id.encode()).hexdigest()[:8], 16)
        
        # Prepare payload (metadata)
        payload = {
            'auction_id': auction_id,
            'title': metadata.get('title', ''),
            'city': metadata.get('city', ''),
            'property_type': metadata.get('property_type', ''),
            'base_price': metadata.get('base_price', 0),
            'surface_sqm': metadata.get('surface_sqm', 0),
        }
        
        # Upsert point
        qdrant_client.upsert(
            collection_name=QDRANT_COLLECTION,
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
            ]
        )
        
        logger.info(
            "stored_in_qdrant",
            auction_id=auction_id,
            point_id=point_id
        )
        
        return str(point_id)
    
    except Exception as e:
        logger.error("qdrant_storage_failed", error=str(e))
        return None


def search_similar(
    query_embedding: List[float],
    top_k: int = 10,
    score_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Search for similar auctions in vector database.
    
    Args:
        query_embedding: Query vector
        top_k: Number of results
        score_threshold: Minimum similarity score
    
    Returns:
        List of similar auctions
    """
    if not qdrant_client:
        return []
    
    try:
        results = qdrant_client.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=query_embedding,
            limit=top_k,
            score_threshold=score_threshold
        )
        
        return [
            {
                'auction_id': hit.payload.get('auction_id'),
                'score': hit.score,
                'metadata': hit.payload
            }
            for hit in results
        ]
    
    except Exception as e:
        logger.error("similarity_search_failed", error=str(e))
        return []
