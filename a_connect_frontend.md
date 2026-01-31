# ERP-Agent REST API Implementation Plan

## Overview
Add FastAPI REST endpoints to the Python backend (`/backend/offer-agent/`) to enable the Next.js frontend to create, review, and approve offers before sending to ERP. Backend will be hosted on AWS Fargate.

## Architecture

```
Next.js (Vercel) → FastAPI REST API (Fargate) → In-memory store + JSON backup → ERP System
                                              ↘ OfferOrchestrator → Product matching/pricing
```

**Key Design Decisions:**
- Use in-memory dict with JSON file backup (simple, no external dependencies, survives restarts via file)
- Add new `process_offer_request_for_review()` method to orchestrator (stops before ERP creation)
- Run API and email automation in same container (shared store)

---

## Files to Create

### 1. API Structure (`src/api/`)

```
src/api/
├── __init__.py
├── main.py                 # FastAPI app with CORS, lifespan
├── dependencies.py         # Dependency injection
├── routes/
│   ├── __init__.py
│   ├── offers.py           # Offer CRUD endpoints
│   └── health.py           # Health check
├── models/
│   ├── __init__.py
│   ├── requests.py         # Pydantic request models
│   └── responses.py        # Pydantic response models
└── services/
    ├── __init__.py
    ├── offer_service.py    # Business logic
    └── pending_store.py    # In-memory + JSON file storage
```

### 2. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/offers/create` | Create offer from form, queue for processing |
| GET | `/api/offers/pending` | List offers awaiting review |
| GET | `/api/offers/status` | Get all offers with status |
| GET | `/api/offers/{id}` | Get single offer details |
| POST | `/api/offers/{id}/send` | Approve and send to ERP |
| DELETE | `/api/offers/{id}` | Delete/reject offer |
| GET | `/health` | Health check for Fargate |

---

## Files to Modify

### 1. `src/core/orchestrator.py`
Add method that runs workflow steps 1-8 (stops before ERP creation):
```python
async def process_offer_request_for_review(self, email_data: Dict) -> WorkflowResult:
    # Runs: parse → extract → find_customer → match_products → calculate_pricing → build_offer
    # Skips: create_offer, verify_offer
```

### 2. `docker/entrypoint.sh`
Add `api` mode as default:
```bash
case "${1:-api}" in
    api) uvicorn src.api.main:app --host 0.0.0.0 --port $PORT ;;
    # existing modes...
esac
```

### 3. `docker/task-definition-exec.json`
- Add `VERCEL_FRONTEND_URL` environment variable
- Add `PENDING_OFFERS_PATH` for JSON backup location (defaults to `/app/data/pending_offers.json`)

---

## Pydantic Models

**Request Models:**
- `CreateOfferRequest`: sender, subject, body, attachments
- `SendToERPRequest`: line_ids (list of lines to approve)

**Response Models:**
- `OrderLineResponse`: product_code, product_name, quantity, unit_price, ai_confidence, original_customer_term
- `PendingOfferResponse`: id, offer_number, customer_name, lines[], status, total_amount
- `OffersListResponse`: offers[], total_count

---

## Storage Schema (In-memory + JSON backup)

```python
# In-memory dict
_pending_offers: Dict[str, PendingOfferResponse] = {}

# JSON file structure (auto-saved on changes)
{
  "offers": {
    "offer_id_1": { ...PendingOfferResponse... },
    "offer_id_2": { ...PendingOfferResponse... }
  },
  "last_updated": "2025-01-29T12:00:00Z"
}
```

**Auto-cleanup:** Offers older than 7 days removed on startup and periodically

---

## CORS Configuration

```python
ALLOWED_ORIGINS = [
    "https://*.vercel.app",
    "http://localhost:3000",
    os.getenv("VERCEL_FRONTEND_URL", ""),
]
```

---

## Implementation Order

1. **Create API models** (`src/api/models/requests.py`, `responses.py`)
2. **Create pending store** (`src/api/services/pending_store.py`) - in-memory + JSON backup
3. **Create offer service** (`src/api/services/offer_service.py`)
4. **Add orchestrator method** (`process_offer_request_for_review` in `src/core/orchestrator.py`)
5. **Create FastAPI app** (`src/api/main.py`) with CORS and lifespan
6. **Create route handlers** (`src/api/routes/offers.py`, `health.py`)
7. **Update Docker config** (entrypoint.sh - add `api` mode)
8. **Test locally** with CSV mode before Fargate deployment

---

## Critical Files Reference

| File | Purpose |
|------|---------|
| `backend/offer-agent/src/core/orchestrator.py` | Add `process_offer_request_for_review()` method |
| `backend/offer-agent/src/core/workflow.py` | WorkflowResult/Context reference |
| `backend/offer-agent/src/domain/offer.py` | Offer/OfferLine domain models |
| `backend/offer-agent/docker/entrypoint.sh` | Add `api` mode |
| `backend/offer-agent/docker/Dockerfile` | Add `data/` volume for JSON backup |
| `frontend/src/app/offers/review/page.tsx` | Expected data structures (OrderLine, PendingOffer)

---

## Verification

1. **Local testing:**
   ```bash
   cd backend/offer-agent
   ERP_TYPE=csv uvicorn src.api.main:app --reload --port 8000
   ```

2. **Test endpoints:**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/api/offers/pending
   ```

3. **Frontend integration:**
   - Start frontend: `cd frontend && npm run dev`
   - Create offer via form
   - Review in pending list
   - Approve/reject

4. **Docker build:**
   ```bash
   docker build -f docker/Dockerfile -t offer-api .
   docker run -p 8000:8000 -e ERP_TYPE=csv offer-api
   ```
