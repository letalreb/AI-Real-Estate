"""
NLP Service main application.
Handles text normalization, entity extraction, and AI ranking.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import structlog
import aiohttp
import os

from .normalizer import normalize_auction_text
from .ner_extractor import extract_entities
from .ranking_engine import calculate_ai_score
from .embeddings import generate_embedding, store_in_qdrant

logger = structlog.get_logger()
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

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


async def save_to_backend(auction_data: Dict[str, Any], ai_score: float, score_breakdown: Dict[str, float], embedding_id: Optional[str]):
    """Save processed auction to backend database."""
    try:
        # Prepare data for backend API
        backend_data = {
            "external_id": auction_data.get("external_id"),
            "title": auction_data.get("title", ""),
            "description": auction_data.get("description", ""),
            "property_type": auction_data.get("property_type", "UNKNOWN"),
            "city": auction_data.get("city", ""),
            "province": auction_data.get("province", ""),
            "address": auction_data.get("address", ""),
            "base_price": auction_data.get("base_price"),
            "auction_date": auction_data.get("auction_date"),
            "auction_round": str(auction_data.get("auction_round", "")),
            "court": auction_data.get("court", ""),
            "status": "ACTIVE",
            "ai_score": ai_score,
            "score_breakdown": score_breakdown,
            "source_url": auction_data.get("url", ""),
            "raw_data": auction_data.get("raw_data", {}),
            "embedding_id": embedding_id
        }
        
        # Add coordinates if available
        if auction_data.get("latitude") and auction_data.get("longitude"):
            backend_data["latitude"] = auction_data["latitude"]
            backend_data["longitude"] = auction_data["longitude"]
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BACKEND_URL}/api/v1/auctions/scraper",
                json=backend_data,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status in [200, 201]:
                    logger.info("saved_to_backend", auction_id=auction_data.get("external_id"))
                    return True
                else:
                    error_text = await response.text()
                    logger.error("backend_save_failed", 
                               status=response.status, 
                               auction_id=auction_data.get("external_id"),
                               error=error_text)
                    return False
    except Exception as e:
        logger.error("backend_save_error", 
                    auction_id=auction_data.get("external_id"), 
                    error=str(e))
        return False


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
    6. Save to backend database
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
        
        # Step 5: Save to backend database
        await save_to_backend(normalized, ai_score, score_breakdown, embedding_id)
        
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
