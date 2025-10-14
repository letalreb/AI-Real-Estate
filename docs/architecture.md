# System Architecture

## Overview

AI Real Estate Auction Analyzer is a distributed system for collecting, analyzing, and presenting Italian real estate auction data with AI-powered ranking.

## Architecture Diagram (ASCII)

```
┌──────────────────────────────────────────────────────────────────┐
│                         FRONTEND TIER                             │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  React SPA (Nginx)                                         │  │
│  │  - Auction List/Map/Detail Views                           │  │
│  │  - User Authentication & Preferences                       │  │
│  │  - Real-time Notifications (WebSocket)                     │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                               │
                               │ HTTPS/WSS
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                        API GATEWAY TIER                           │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Backend API (FastAPI)                                     │  │
│  │  - RESTful Endpoints (OpenAPI)                             │  │
│  │  - JWT Authentication                                      │  │
│  │  - WebSocket Server                                        │  │
│  │  - Rate Limiting & CORS                                    │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
         │              │              │              │
         │              │              │              │
    ┌────┘              │              │              └────┐
    │                   │              │                   │
    ▼                   ▼              ▼                   ▼
┌─────────┐   ┌──────────────┐  ┌──────────┐    ┌────────────┐
│ Postgres│   │ NLP Service  │  │  Qdrant  │    │   Redis    │
│ PostGIS │   │   (Python)   │  │ (Vector) │    │  (Cache)   │
│         │   │              │  │          │    │            │
│ • Users │   │ • spaCy NER  │  │ • Search │    │ • Sessions │
│ • Auc.  │   │ • Embeddings │  │ • Similar│    │ • Queue    │
│ • Prefs │   │ • Ranking AI │  │          │    │            │
└─────────┘   └──────────────┘  └──────────┘    └────────────┘
                   ▲
                   │
                   │ HTTP
                   │
           ┌───────┴──────┐
           │   Scraper    │
           │   Service    │
           │              │
           │ • PVP Spider │
           │ • Rate Limit │
           │ • Robots.txt │
           └──────────────┘
                   ▲
                   │
                   │ HTTPS (polite)
                   │
           ┌───────┴──────┐
           │ pvp.giustizia│
           │     .it      │
           │ (Data Source)│
           └──────────────┘
```

## Component Descriptions

### 1. Frontend (React SPA)

**Technology:** React 18, TypeScript, Vite, Leaflet

**Responsibilities:**
- User interface for browsing auctions
- Interactive map visualization
- Search and filtering
- User authentication (JWT)
- WebSocket client for real-time notifications
- Responsive design (mobile-friendly)

**Key Features:**
- Auction list with pagination and filters
- Map view with geographic clustering
- Detailed auction pages with AI score
- User preferences and saved searches
- Real-time notifications

### 2. Backend API (FastAPI)

**Technology:** Python 3.11, FastAPI, SQLAlchemy, Pydantic

**Responsibilities:**
- RESTful API endpoints
- Authentication & authorization (JWT)
- Business logic orchestration
- WebSocket server for notifications
- Database operations (CRUD)
- API rate limiting

**Endpoints:**
- `GET /api/v1/auctions` - List auctions with filters
- `GET /api/v1/auctions/{id}` - Get auction details
- `GET /api/v1/auctions/search/text` - Text search
- `GET /api/v1/auctions/nearby/{id}` - Geographic search
- `POST /api/v1/users/register` - User registration
- `POST /api/v1/users/login` - User login
- `GET /api/v1/preferences` - User preferences
- `WS /ws/notifications` - Real-time notifications

### 3. Database (PostgreSQL + PostGIS)

**Technology:** PostgreSQL 15, PostGIS extension

**Responsibilities:**
- Persistent data storage
- Geospatial queries
- ACID transactions
- Full-text search

**Key Tables:**
- `users` - User accounts
- `auctions` - Auction data with geospatial info
- `search_preferences` - Saved searches
- `notifications` - User notifications
- `scraping_logs` - Scraper activity logs

### 4. NLP Service (Python)

**Technology:** Python 3.11, spaCy, Sentence Transformers, scikit-learn

**Responsibilities:**
- Natural Language Processing
- Named Entity Recognition (NER)
- Text embedding generation
- AI ranking calculation
- Market value estimation

**NLP Pipeline:**
1. **Text Preprocessing:** Clean and normalize Italian text
2. **Entity Extraction:** 
   - Property type (appartamento, villa, etc.)
   - Location (city, address)
   - Measurements (surface in sqm, rooms)
   - Prices (base price, estimates)
   - Dates (auction date)
3. **Embedding Generation:** Create vector representations for semantic search
4. **AI Ranking:** Calculate 0-100 convenience score based on:
   - Price discount vs market value (30%)
   - Location desirability (25%)
   - Property condition (15%)
   - Legal complexity (15%)
   - Liquidity potential (15%)

### 5. Vector Database (Qdrant)

**Technology:** Qdrant vector database

**Responsibilities:**
- Store text embeddings
- Semantic similarity search
- Vector indexing and retrieval
- Fast nearest neighbor queries

**Use Cases:**
- "Find auctions similar to this one"
- Semantic text search
- Recommendation engine

### 6. Scraper Service (Python)

**Technology:** Python 3.11, aiohttp, BeautifulSoup, Redis

**Responsibilities:**
- Collect auction data from pvp.giustizia.it
- Respect robots.txt and rate limits
- Parse HTML/JSON responses
- Publish data to NLP service
- Error handling and retry logic

**Politeness Features:**
- Max 30 requests/minute
- 1-second delay between requests
- robots.txt compliance
- Exponential backoff on errors
- Caching to avoid duplicate requests

### 7. Cache & Queue (Redis)

**Technology:** Redis 7

**Responsibilities:**
- Cache frequently accessed data
- Session storage
- Message queue for async tasks
- Rate limiting counters
- WebSocket connection tracking

## Data Flow

### 1. Scraping Flow

```
pvp.giustizia.it
    │
    │ (1) HTTP GET with rate limiting
    ▼
Scraper Service
    │
    │ (2) Parse HTML/JSON
    │ (3) Extract raw data
    ▼
NLP Service
    │
    │ (4) NER, embeddings, scoring
    ▼
Backend API
    │
    │ (5) Save to PostgreSQL
    │ (6) Index in Qdrant
    ▼
Database + Vector DB
```

### 2. User Query Flow

```
User (Browser)
    │
    │ (1) HTTP GET /api/v1/auctions?city=Roma
    ▼
Backend API
    │
    │ (2) Check Redis cache
    │ (3) Query PostgreSQL
    │ (4) Apply filters
    ▼
Database
    │
    │ (5) Return results
    ▼
Backend API
    │
    │ (6) Cache in Redis
    │ (7) JSON response
    ▼
User (Browser)
```

### 3. Semantic Search Flow

```
User Query: "appartamento centro storico"
    │
    ▼
Backend API
    │
    │ (1) Forward to NLP service
    ▼
NLP Service
    │
    │ (2) Generate query embedding
    ▼
Qdrant
    │
    │ (3) Vector similarity search
    │ (4) Return top K auction IDs
    ▼
Backend API
    │
    │ (5) Fetch full auction details
    ▼
PostgreSQL
    │
    │ (6) Return enriched results
    ▼
User (Browser)
```

### 4. Notification Flow

```
New Auction Detected
    │
    ▼
Backend API
    │
    │ (1) Match against user preferences
    │ (2) Create notification records
    ▼
Database
    │
    │ (3) Trigger WebSocket broadcast
    ▼
WebSocket Server
    │
    │ (4) Send to active connections
    ▼
Connected Users (Real-time)
```

## Scaling Considerations

### Horizontal Scaling

- **Backend API**: Stateless, can run multiple replicas behind load balancer
- **NLP Service**: CPU-intensive, scale based on processing queue depth
- **Scraper**: Run as scheduled job (cron), or multiple instances with coordination
- **Frontend**: Static files, served via CDN

### Vertical Scaling

- **PostgreSQL**: Optimize with read replicas for heavy read workloads
- **Qdrant**: Increase memory for larger vector indices
- **Redis**: Increase memory for larger cache

### Performance Optimizations

1. **Caching Strategy:**
   - API responses cached 5 minutes
   - Search results cached 3 minutes
   - Market stats cached 1 hour

2. **Database Indexes:**
   - B-tree index on `city`, `property_type`, `status`
   - GiST index on `coordinates` (PostGIS)
   - Covering index on frequently queried columns

3. **Connection Pooling:**
   - PostgreSQL: Pool size 10, max overflow 20
   - Redis: Connection pool enabled

4. **Async Processing:**
   - Scraping runs asynchronously
   - NLP processing queued via Redis
   - WebSocket broadcasts non-blocking

## Security Architecture

### Authentication & Authorization

- **JWT Tokens:** Stateless authentication with 24-hour expiration
- **Password Hashing:** bcrypt with appropriate work factor
- **Role-Based Access:** User and Admin roles

### Network Security

- **HTTPS Only:** TLS 1.3 enforced in production
- **CORS:** Strict origin whitelist
- **Rate Limiting:** Per-IP and per-user limits
- **Input Validation:** Pydantic schemas for all inputs

### Data Protection

- **Encryption at Rest:** Database encryption enabled
- **Secure Sessions:** HTTP-only cookies
- **SQL Injection Protection:** Parameterized queries via ORM
- **XSS Prevention:** Content Security Policy headers

## Monitoring & Observability

### Metrics (Prometheus)

- Request rate and latency (P50, P95, P99)
- Error rates by endpoint
- Database query performance
- Scraping success/failure rates
- AI scoring distribution

### Logs (Structured JSON)

- Application logs with correlation IDs
- Access logs with user context
- Error logs with stack traces
- Audit logs for sensitive operations

### Health Checks

- `/health` endpoint for all services
- Database connectivity check
- External service dependencies
- Disk space and memory usage

## Deployment Architecture

### Development

- Docker Compose for local development
- Hot reload for code changes
- Local PostgreSQL, Redis, Qdrant

### Staging

- Kubernetes cluster (3 nodes)
- Separate namespace per environment
- Automated CI/CD pipeline
- Preview deployments for PRs

### Production

- Multi-region Kubernetes cluster
- High availability (3+ replicas per service)
- Automated backups (daily)
- Disaster recovery plan
- CDN for frontend assets
- Managed database (RDS/CloudSQL)
- Monitoring and alerting (Prometheus + Grafana)

## Technology Choices Rationale

### Why FastAPI?
- Modern async Python framework
- Automatic OpenAPI documentation
- High performance (comparable to Node.js)
- Excellent typing support with Pydantic

### Why PostgreSQL + PostGIS?
- Mature, reliable relational database
- PostGIS for geospatial queries
- ACID compliance
- Excellent performance for our data size

### Why Qdrant?
- Purpose-built for vector search
- Fast similarity queries
- Easy integration with Python
- Open-source

### Why React?
- Large ecosystem and community
- Mature state management options
- Excellent TypeScript support
- Component reusability

### Why Docker + Kubernetes?
- Consistent environments (dev = prod)
- Easy scaling and orchestration
- Industry standard
- Extensive tooling

---

**Last Updated:** October 14, 2025  
**Version:** 1.0
