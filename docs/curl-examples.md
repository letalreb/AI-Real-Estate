# API cURL Examples

Complete collection of cURL commands for testing the AI Real Estate Auction Analyzer API.

## Table of Contents

1. [Authentication](#authentication)
2. [Auctions](#auctions)
3. [Search](#search)
4. [User Preferences](#user-preferences)
5. [Statistics](#statistics)
6. [WebSocket](#websocket)

---

## Authentication

### Register New User

```bash
curl -X POST http://localhost:8000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "mario.rossi@example.com",
    "password": "SecurePass123!"
  }'
```

**Expected Response (201 Created):**
```json
{
  "id": 1,
  "email": "mario.rossi@example.com",
  "is_active": true,
  "is_admin": false,
  "created_at": "2025-10-14T10:30:00Z"
}
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "mario.rossi@example.com",
    "password": "SecurePass123!"
  }'
```

**Expected Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Save the token for authenticated requests:**
```bash
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Get Current User Profile

```bash
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## Auctions

### List All Auctions (Paginated)

```bash
curl "http://localhost:8000/api/v1/auctions?page=1&page_size=20"
```

**Response:**
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "pages": 8
}
```

### Filter Auctions by City

```bash
curl "http://localhost:8000/api/v1/auctions?city=Roma&page_size=10"
```

### Filter by Property Type

```bash
curl "http://localhost:8000/api/v1/auctions?property_type=Appartamento"
```

### Filter by Price Range

```bash
curl "http://localhost:8000/api/v1/auctions?min_price=50000&max_price=200000"
```

### Filter by AI Score (High Quality)

```bash
curl "http://localhost:8000/api/v1/auctions?min_score=75"
```

### Combined Filters

```bash
curl "http://localhost:8000/api/v1/auctions?\
city=Milano&\
property_type=Appartamento&\
min_price=100000&\
max_price=300000&\
min_score=70&\
page=1&\
page_size=20"
```

### Get Specific Auction Details

```bash
curl http://localhost:8000/api/v1/auctions/123
```

**Response:**
```json
{
  "id": 123,
  "external_id": "PVP-RM-00123",
  "title": "Appartamento - Roma - 85mq",
  "description": "Immobile di pregio situato in zona centrale",
  "property_type": "Appartamento",
  "city": "Roma",
  "province": "RM",
  "address": "Via Roma 42",
  "latitude": 41.9028,
  "longitude": 12.4964,
  "surface_sqm": 85.0,
  "rooms": 3,
  "bathrooms": 2,
  "floor": 3,
  "base_price": 180000.0,
  "current_price": 180000.0,
  "estimated_value": 250000.0,
  "auction_date": "2025-11-15T10:00:00Z",
  "court": "Tribunale di Roma",
  "status": "active",
  "ai_score": 78.5,
  "score_breakdown": {
    "price_discount": 28.0,
    "location_score": 85,
    "property_condition": 70,
    "legal_complexity": 65,
    "liquidity_potential": 80
  },
  "source_url": "https://pvp.giustizia.it/pvp/it/dettaglio.page?idAnnuncio=123",
  "created_at": "2025-10-14T08:00:00Z",
  "updated_at": "2025-10-14T08:00:00Z"
}
```

---

## Search

### Text Search

```bash
curl "http://localhost:8000/api/v1/auctions/search/text?q=appartamento+centro+storico"
```

### Text Search with Pagination

```bash
curl "http://localhost:8000/api/v1/auctions/search/text?\
q=villa+giardino&\
page=1&\
page_size=10"
```

### Find Nearby Auctions

```bash
# Find auctions within 10km of auction #123
curl "http://localhost:8000/api/v1/auctions/nearby/123?radius_km=10&limit=20"
```

### Find Nearby with Custom Radius

```bash
# Find auctions within 5km
curl "http://localhost:8000/api/v1/auctions/nearby/123?radius_km=5&limit=10"
```

---

## User Preferences

### Create Search Preference

```bash
curl -X POST http://localhost:8000/api/v1/preferences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Appartamenti Roma Centro",
    "filters": {
      "cities": ["Roma"],
      "property_types": ["Appartamento"],
      "min_score": 75,
      "max_price": 250000
    },
    "notify": true
  }'
```

**Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 1,
  "name": "Appartamenti Roma Centro",
  "filters": {
    "cities": ["Roma"],
    "property_types": ["Appartamento"],
    "min_score": 75,
    "max_price": 250000
  },
  "notify": true,
  "is_active": true,
  "created_at": "2025-10-14T11:00:00Z",
  "updated_at": "2025-10-14T11:00:00Z"
}
```

### List User Preferences

```bash
curl http://localhost:8000/api/v1/preferences \
  -H "Authorization: Bearer $TOKEN"
```

### Get Specific Preference

```bash
curl http://localhost:8000/api/v1/preferences/1 \
  -H "Authorization: Bearer $TOKEN"
```

### Update Preference

```bash
curl -X PUT http://localhost:8000/api/v1/preferences/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Appartamenti Roma - Updated",
    "filters": {
      "cities": ["Roma", "Milano"],
      "property_types": ["Appartamento"],
      "min_score": 80,
      "max_price": 300000
    },
    "notify": true
  }'
```

### Disable Notifications for Preference

```bash
curl -X PUT http://localhost:8000/api/v1/preferences/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notify": false
  }'
```

### Delete Preference

```bash
curl -X DELETE http://localhost:8000/api/v1/preferences/1 \
  -H "Authorization: Bearer $TOKEN"
```

---

## Statistics

### Get Market Statistics (All Italy)

```bash
curl http://localhost:8000/api/v1/stats/market
```

**Response:**
```json
{
  "total_auctions": 1247,
  "active_auctions": 1247,
  "avg_base_price": 156780.50,
  "avg_score": 68.4,
  "property_type_distribution": {
    "Appartamento": 543,
    "Villa": 187,
    "Attico": 98,
    "Locale Commerciale": 145,
    "Ufficio": 112,
    "Box": 98,
    "Terreno": 64
  },
  "city_distribution": {
    "Roma": 234,
    "Milano": 198,
    "Napoli": 145,
    "Torino": 123,
    "Bologna": 98
  },
  "price_ranges": {
    "0-50k": 287,
    "50k-100k": 345,
    "100k-250k": 412,
    "250k-500k": 156,
    "500k+": 47
  }
}
```

### Get Market Statistics for Specific City

```bash
curl "http://localhost:8000/api/v1/stats/market?city=Roma"
```

---

## WebSocket

### Connect to WebSocket for Notifications

**Using wscat (install: `npm install -g wscat`):**

```bash
# Replace TOKEN with your JWT token
wscat -c "ws://localhost:8000/ws/notifications?token=$TOKEN"
```

**Using JavaScript:**

```javascript
const token = 'YOUR_JWT_TOKEN_HERE';
const ws = new WebSocket(`ws://localhost:8000/ws/notifications?token=${token}`);

ws.onopen = () => {
  console.log('Connected to notification server');
  
  // Send ping to keep connection alive
  setInterval(() => {
    ws.send(JSON.stringify({ type: 'ping' }));
  }, 30000);
};

ws.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  console.log('Received notification:', notification);
  
  // Handle different notification types
  switch(notification.type) {
    case 'new_auction':
      console.log('New auction matching your preferences!');
      break;
    case 'price_drop':
      console.log('Price dropped on saved auction!');
      break;
    case 'ending_soon':
      console.log('Auction ending soon!');
      break;
    case 'pong':
      console.log('Pong received');
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from notification server');
};
```

**Example Notification Message:**

```json
{
  "type": "new_auction",
  "title": "New Auction in Roma",
  "message": "A new Appartamento matching your preferences is available",
  "data": {
    "auction_id": 456,
    "city": "Roma",
    "base_price": 185000,
    "ai_score": 82
  },
  "timestamp": "2025-10-14T12:34:56Z"
}
```

---

## Advanced Examples

### Complete User Flow Example

```bash
#!/bin/bash

# 1. Register and login
echo "Registering user..."
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}')

echo "Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "Token: $TOKEN"

# 2. Get auctions
echo -e "\nFetching auctions..."
curl -s "http://localhost:8000/api/v1/auctions?min_score=70&page_size=5" | jq '.'

# 3. Create preference
echo -e "\nCreating preference..."
curl -s -X POST http://localhost:8000/api/v1/preferences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"High Quality Apartments",
    "filters":{"min_score":75,"property_types":["Appartamento"]},
    "notify":true
  }' | jq '.'

# 4. Get user preferences
echo -e "\nFetching preferences..."
curl -s http://localhost:8000/api/v1/preferences \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

### Batch Download Auctions

```bash
#!/bin/bash

# Download all auctions page by page
PAGE=1
TOTAL_PAGES=1

while [ $PAGE -le $TOTAL_PAGES ]; do
  echo "Downloading page $PAGE..."
  
  RESPONSE=$(curl -s "http://localhost:8000/api/v1/auctions?page=$PAGE&page_size=100")
  
  # Save to file
  echo $RESPONSE | jq '.' > "auctions_page_${PAGE}.json"
  
  # Get total pages from first response
  if [ $PAGE -eq 1 ]; then
    TOTAL_PAGES=$(echo $RESPONSE | jq '.pages')
  fi
  
  PAGE=$((PAGE + 1))
  
  # Be polite, wait between requests
  sleep 1
done

echo "Downloaded $TOTAL_PAGES pages"
```

### Performance Testing

```bash
# Test API response time
time curl -s http://localhost:8000/api/v1/auctions?page_size=20 > /dev/null

# Load test (requires 'ab' - Apache Bench)
ab -n 1000 -c 10 http://localhost:8000/api/v1/auctions
```

---

## Common Response Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 204 | No Content | Resource deleted successfully |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

---

## Testing Tips

1. **Set variables for repeated use:**
   ```bash
   export API_URL="http://localhost:8000/api/v1"
   export TOKEN="your_token_here"
   ```

2. **Pretty print JSON with jq:**
   ```bash
   curl $API_URL/auctions | jq '.'
   ```

3. **Save responses to files:**
   ```bash
   curl $API_URL/auctions > auctions.json
   ```

4. **Include response headers:**
   ```bash
   curl -i $API_URL/auctions
   ```

5. **Verbose mode for debugging:**
   ```bash
   curl -v $API_URL/auctions
   ```

6. **Test with invalid data:**
   ```bash
   curl -X POST $API_URL/users/register \
     -H "Content-Type: application/json" \
     -d '{"email":"invalid","password":"123"}' \
     | jq '.'
   ```

---

**Last Updated:** October 14, 2025
