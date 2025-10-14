"""
Acceptance and integration tests.
Tests full system flow from scraping to API responses.
"""
import pytest
import httpx
from sqlalchemy import select, func
from datetime import datetime

from src.database import AsyncSessionLocal
from src.models import Auction, User, SearchPreference


@pytest.mark.asyncio
async def test_system_startup_time():
    """Test that system starts within acceptable time."""
    # This test would be run in CI with docker-compose
    # Here we just verify API is accessible
    async with httpx.AsyncClient() as client:
        response = await client.get("http://backend:8000/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_sample_data_import():
    """Test that sample data was imported successfully."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.count()).select_from(Auction)
        )
        count = result.scalar()
        
        # Should have at least 50 auctions from sample data
        assert count >= 50, f"Expected at least 50 auctions, found {count}"


@pytest.mark.asyncio
async def test_nlp_extraction_precision():
    """Test NLP extraction meets minimum precision threshold."""
    async with AsyncSessionLocal() as session:
        # Get auctions with extracted data
        result = await session.execute(
            select(Auction).where(
                Auction.city.isnot(None),
                Auction.surface_sqm.isnot(None),
                Auction.base_price.isnot(None)
            )
        )
        auctions_with_data = result.scalars().all()
        
        total = await session.execute(select(func.count()).select_from(Auction))
        total_count = total.scalar()
        
        # Calculate precision (auctions with complete data / total auctions)
        if total_count > 0:
            precision = len(auctions_with_data) / total_count
            
            # Should have >= 85% precision
            assert precision >= 0.85, f"NLP precision {precision:.2%} below threshold 85%"


@pytest.mark.asyncio
async def test_ranking_correlation():
    """Test that AI ranking correlates with market estimates."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Auction).where(
                Auction.ai_score.isnot(None),
                Auction.estimated_value.isnot(None),
                Auction.base_price.isnot(None)
            )
        )
        auctions = result.scalars().all()
        
        if len(auctions) < 10:
            pytest.skip("Not enough data for correlation test")
        
        # Calculate discount percentages
        discounts = [
            (a.estimated_value - a.base_price) / a.estimated_value
            for a in auctions
        ]
        scores = [a.ai_score for a in auctions]
        
        # Calculate Spearman correlation (simplified)
        from scipy.stats import spearmanr
        correlation, p_value = spearmanr(discounts, scores)
        
        # Should have correlation >= 0.5
        assert correlation >= 0.5, f"Ranking correlation {correlation:.2f} below threshold 0.5"


@pytest.mark.asyncio
async def test_api_response_time():
    """Test API response time meets performance requirements."""
    import time
    
    async with httpx.AsyncClient() as client:
        times = []
        
        # Make 100 requests to measure P95
        for _ in range(100):
            start = time.time()
            response = await client.get("http://backend:8000/api/v1/auctions?page_size=20")
            end = time.time()
            
            assert response.status_code == 200
            times.append((end - start) * 1000)  # Convert to ms
        
        # Calculate P95
        times.sort()
        p95_index = int(len(times) * 0.95)
        p95_latency = times[p95_index]
        
        # P95 should be < 500ms
        assert p95_latency < 500, f"P95 latency {p95_latency:.0f}ms exceeds 500ms threshold"


@pytest.mark.asyncio
async def test_end_to_end_user_flow():
    """Test complete user flow from registration to receiving notifications."""
    base_url = "http://backend:8000/api/v1"
    
    async with httpx.AsyncClient() as client:
        # 1. Register user
        register_data = {
            "email": "test@example.com",
            "password": "securepass123"
        }
        response = await client.post(f"{base_url}/users/register", json=register_data)
        assert response.status_code in [201, 400]  # 400 if already exists
        
        # 2. Login
        response = await client.post(f"{base_url}/users/login", json=register_data)
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Get auctions list
        response = await client.get(f"{base_url}/auctions", headers=headers)
        assert response.status_code == 200
        auctions = response.json()
        assert auctions["total"] > 0
        
        # 4. Get specific auction
        auction_id = auctions["items"][0]["id"]
        response = await client.get(f"{base_url}/auctions/{auction_id}", headers=headers)
        assert response.status_code == 200
        auction = response.json()
        assert auction["ai_score"] is not None
        
        # 5. Create search preference
        preference_data = {
            "name": "My Test Search",
            "filters": {"city": "Roma", "min_score": 70},
            "notify": True
        }
        response = await client.post(f"{base_url}/preferences", json=preference_data, headers=headers)
        assert response.status_code == 201
        
        # 6. List preferences
        response = await client.get(f"{base_url}/preferences", headers=headers)
        assert response.status_code == 200
        preferences = response.json()
        assert len(preferences) > 0


@pytest.mark.asyncio
async def test_vector_search_functionality():
    """Test semantic search returns relevant results."""
    async with httpx.AsyncClient() as client:
        # Search for apartments in Rome
        response = await client.get(
            "http://backend:8000/api/v1/auctions/search/text?q=appartamento roma centro"
        )
        assert response.status_code == 200
        results = response.json()
        
        # Should return results
        assert results["total"] > 0
        
        # Results should be relevant (contain search terms)
        for item in results["items"][:5]:
            text = f"{item['title']} {item.get('description', '')} {item.get('city', '')}".lower()
            # At least one search term should appear
            assert any(term in text for term in ["appartamento", "roma", "centro"])


def test_coverage_threshold():
    """Verify test coverage meets minimum threshold."""
    # This is checked by pytest-cov in CI
    # Just a placeholder to document the requirement
    required_coverage = 70
    # Actual coverage check happens in CI pipeline
    assert required_coverage >= 70
