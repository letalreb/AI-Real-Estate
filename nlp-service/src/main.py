"""
NLP Service main application.
Handles text normalization, entity extraction, and AI ranking.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import structlog

from .normalizer import normalize_auction_text
from .ner_extractor import extract_entities
from .ranking_engine import calculate_ai_score
from .embeddings import generate_embedding, store_in_qdrant

logger = structlog.get_logger()

app = FastAPI(
    title="AI Real Estate NLP Service",
    description="NLP processing for auction data",
    version="1.0.0"
)


class AuctionInput(BaseModel):
    """Input schema for auction processing."""
    external_id: str
    title: str
    description: Optional[str] = None
    full_text: Optional[str] = None
    city: Optional[str] = None
    price_text: Optional[str] = None
    source_url: Optional[str] = None


class ProcessedAuction(BaseModel):
    """Output schema for processed auction."""
    external_id: str
    normalized_data: Dict[str, Any]
    extracted_entities: Dict[str, Any]
    ai_score: float
    score_breakdown: Dict[str, float]
    embedding_id: Optional[str] = None


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "nlp-service",
        "version": "1.0.0"
    }


@app.post("/process", response_model=ProcessedAuction)
async def process_auction(auction: AuctionInput):
    """
    Process auction data through NLP pipeline.
    
    Steps:
    1. Normalize text
    2. Extract entities (NER)
    3. Calculate AI ranking score
    4. Generate embeddings
    5. Store in vector database
    """
    try:
        logger.info("processing_auction", auction_id=auction.external_id)
        
        # Step 1: Normalize text
        normalized = normalize_auction_text(auction.dict())
        
        # Step 2: Extract entities
        entities = extract_entities(
            title=auction.title,
            description=auction.description or "",
            full_text=auction.full_text or ""
        )
        
        # Merge extracted entities with input
        normalized.update(entities)
        
        # Step 3: Calculate AI score
        ai_score, score_breakdown = calculate_ai_score(normalized)
        
        # Step 4: Generate embeddings and store
        embedding_text = f"{auction.title} {auction.description or ''}"
        embedding_id = None
        
        try:
            embedding = generate_embedding(embedding_text)
            embedding_id = await store_in_qdrant(
                auction.external_id,
                embedding,
                normalized
            )
        except Exception as e:
            logger.warning("embedding_failed", error=str(e))
        
        logger.info(
            "auction_processed",
            auction_id=auction.external_id,
            ai_score=ai_score
        )
        
        return ProcessedAuction(
            external_id=auction.external_id,
            normalized_data=normalized,
            extracted_entities=entities,
            ai_score=ai_score,
            score_breakdown=score_breakdown,
            embedding_id=embedding_id
        )
    
    except Exception as e:
        logger.error(
            "processing_failed",
            auction_id=auction.external_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract-entities")
async def extract_entities_endpoint(text: str):
    """Extract entities from raw text."""
    try:
        entities = extract_entities(text, "", "")
        return entities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/calculate-score")
async def calculate_score_endpoint(data: Dict[str, Any]):
    """Calculate AI score for given data."""
    try:
        score, breakdown = calculate_ai_score(data)
        return {
            "ai_score": score,
            "score_breakdown": breakdown
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
