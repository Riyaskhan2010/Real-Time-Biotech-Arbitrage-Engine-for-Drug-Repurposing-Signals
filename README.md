# BioArbitrage — Real-Time Biotech Arbitrage Engine for Drug Repurposing Signals

> **Research decision-support tool only.**
> This platform does NOT diagnose patients, prescribe medicines, or provide medical treatment recommendations.
> All demo data is clearly labelled simulated data — not real clinical conclusions.

---

## What it does

BioArbitrage is a biomedical research intelligence platform that helps researchers discover potential drug-repurposing signals by cross-referencing biological pathways, molecular targets, and published research associations.

**Core pipeline:**
```
Research Data → Ingestion → NLP Extraction → Drug/Disease Identification
→ Cross-Source Evidence Matching → Signal Detection → Evidence Scoring
→ Explainable AI → Researcher Dashboard
```

---

## Tech Stack

| Layer      | Technology                                                  |
|------------|-------------------------------------------------------------|
| Frontend   | React 18, TypeScript, Tailwind CSS, Recharts, Zustand, Vite |
| Backend    | Python 3.11+, FastAPI, SQLAlchemy, SQLite                   |
| Auth       | JWT (python-jose), bcrypt (passlib)                         |
| AI Service | OpenAI GPT-4o-mini (optional) + heuristic fallback          |
| Database   | SQLite (MVP) — PostgreSQL-ready via DATABASE_URL env var     |

---

## Project Structure

```
.
├── backend/
│   ├── main.py                  # FastAPI entry point (auto-seeds on first run)
│   ├── requirements.txt
│   ├── .env                     # Environment variables (copy from .env.example)
│   ├── .env.example
│   └── app/
│       ├── config.py            # Pydantic settings
│       ├── database.py          # SQLAlchemy engine + session
│       ├── models/              # SQLAlchemy ORM models
│       │   ├── user.py
│       │   ├── drug.py
│       │   ├── disease.py
│       │   ├── signal.py        # RepurposingSignal
│       │   ├── evidence.py
│       │   ├── alert.py
│       │   └── research_source.py
│       ├── schemas/
│       │   └── schemas.py       # Pydantic request/response schemas
│       ├── api/                 # FastAPI routers
│       │   ├── auth.py          # POST /api/auth/token, GET /api/auth/me
│       │   ├── dashboard.py     # GET /api/dashboard
│       │   ├── signals.py       # GET /api/signals, /api/signals/{id}, /explain
│       │   ├── drugs.py         # GET /api/drugs, /api/drugs/{id}/signals
│       │   ├── diseases.py      # GET /api/diseases, /api/diseases/{id}/signals
│       │   ├── evidence.py      # GET /api/evidence
│       │   └── alerts.py        # GET/PATCH /api/alerts
│       ├── services/
│       │   └── ai_service.py    # AI abstraction (OpenAI + heuristic fallback)
│       ├── data/
│       │   ├── seed_data.py     # Demo data definitions
│       │   └── seeder.py        # Database seeder
│       └── utils/
│           └── auth.py          # JWT + password utilities
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts           # Proxies /api → localhost:8000
│   ├── tailwind.config.js
│   └── src/
│       ├── main.tsx
│       ├── App.tsx              # Router setup
│       ├── index.css
│       ├── types/index.ts       # TypeScript interfaces
│       ├── api/                 # Axios API client + typed wrappers
│       ├── store/authStore.ts   # Zustand auth state
│       ├── components/          # Sidebar, Header, Layout, SignalCard, Charts, UI
│       └── pages/               # Dashboard, Signals, SignalDetail, Drugs,
│                                #   Diseases, Evidence, Alerts, Settings, Login
│
├── .gitignore
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm 9+

### 1. Backend setup

```powershell
# From project root
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1        # Windows PowerShell
# source venv/bin/activate          # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Copy environment file (already done — edit if needed)
# The .env file is pre-configured for local SQLite development

# Start the backend (auto-seeds the database on first run)
uvicorn main:app --reload --port 8000
```

The backend will:
1. Create `bioarbitrage.db` (SQLite) automatically
2. Seed all demo data on first startup
3. Be available at `http://localhost:8000`
4. Serve API docs at `http://localhost:8000/docs`

### 2. Frontend setup

```powershell
# Open a second terminal, from project root
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

Vite proxies all `/api/*` requests to `http://localhost:8000` automatically — no CORS configuration needed during development.

---

## Demo Login Credentials

| Role       | Username          | Password    |
|------------|-------------------|-------------|
| Researcher | demo_researcher   | demo1234    |
| Admin      | demo_admin        | admin1234   |

Or use the email: `researcher@bioarbitrage.demo` / `demo1234`

---

## Demo Data

The database is pre-seeded with realistic but clearly labelled demo data:

| Entity             | Count | Examples                                                     |
|--------------------|-------|--------------------------------------------------------------|
| Drugs              | 8     | Metformin, Rapamycin, Sildenafil, Doxycycline, Lithium, ...  |
| Diseases           | 7     | Alzheimer's, Glioblastoma, TNBC, Multiple Sclerosis, ...     |
| Signals            | 8     | Metformin→AD (82/100), Lithium→AD (74/100), ...              |
| Evidence items     | 6     | Research papers, clinical trial records                      |
| Research sources   | 5     | PubMed, bioRxiv, ClinicalTrials.gov (extension points)       |
| Alerts             | 3     | Pre-seeded for demo researcher                               |

All demo records are tagged `is_demo_data: true` and `data_source: "demo"`.

---

## Demo Flow (End-to-End)

1. Open `http://localhost:5173` → redirected to Login
2. Sign in with `demo_researcher / demo1234`
3. **Dashboard** — 6 stat cards, signal trend chart, recent + high-confidence signals
4. Click any signal card → **Signal Detail** page
   - Drug → Disease relationship display
   - Evidence score (0–100) with breakdown
   - Click **"Regenerate AI Explanation"** → Explainable AI panel
   - Explanation factors (strong / moderate / weak / negative)
   - Supporting evidence with source links
   - Drug context & Disease context panels
5. Navigate to **Signals** → filter by confidence, search, sort
6. Navigate to **Drugs** → expand Metformin → see repurposing signals
7. Navigate to **Diseases** → expand Alzheimer's → see candidate drugs
8. Navigate to **Evidence** → filter by type (clinical trial / research paper)
9. Navigate to **Research Alerts** → unread alerts, mark read / dismiss
10. Navigate to **Settings** → profile, security info, data source status

---

## API Reference

All endpoints require `Authorization: Bearer <token>` except `/api/auth/token`.

| Method | Endpoint                          | Description                          |
|--------|-----------------------------------|--------------------------------------|
| POST   | `/api/auth/token`                 | Login (form: username, password)     |
| GET    | `/api/auth/me`                    | Current user                         |
| GET    | `/api/dashboard`                  | Dashboard stats + trend + signals    |
| GET    | `/api/signals`                    | List signals (filter, search, sort)  |
| GET    | `/api/signals/{id}`               | Signal detail + evidence             |
| GET    | `/api/signals/{id}/explain`       | AI explanation for signal            |
| GET    | `/api/drugs`                      | List drugs (search, filter)          |
| GET    | `/api/drugs/{id}/signals`         | Signals for a drug                   |
| GET    | `/api/diseases`                   | List diseases                        |
| GET    | `/api/diseases/{id}/signals`      | Signals for a disease                |
| GET    | `/api/evidence`                   | Evidence explorer (filter, search)   |
| GET    | `/api/alerts`                     | User alerts                          |
| PATCH  | `/api/alerts/{id}/read`           | Mark alert read                      |
| PATCH  | `/api/alerts/{id}/dismiss`        | Dismiss alert                        |
| PATCH  | `/api/alerts/mark-all-read`       | Mark all alerts read                 |

Interactive docs: `http://localhost:8000/docs`

---

## AI Service

The AI layer is fully abstracted in `backend/app/services/ai_service.py`.

**Without API key** (default): heuristic fallback — fully functional, uses structured demo data and keyword matching.

**With OpenAI key**: set `OPENAI_API_KEY` in `backend/.env` — uses GPT-4o-mini for signal explanations, entity extraction, and evidence summarization.

```env
# backend/.env
OPENAI_API_KEY=sk-...your-key-here...
```

No restart needed — the service detects the key at startup.

---

## Configuration

All configuration is in `backend/.env`:

```env
APP_ENV=development
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DATABASE_URL=sqlite:///./bioarbitrage.db   # Switch to postgresql://... for prod
OPENAI_API_KEY=                            # Optional
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## Production Build

```powershell
# Build frontend static files
cd frontend
npm run build
# Output: frontend/dist/

# Run backend in production mode
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

For production, serve `frontend/dist/` via nginx or a CDN and point `ALLOWED_ORIGINS` to your domain.

---

## Future Extension Points

The architecture is designed for easy extension. All integration points are marked in code with `# INTEGRATION POINT` or `# extension point` comments.

| Feature                          | Location                              |
|----------------------------------|---------------------------------------|
| PubMed live ingestion            | `app/models/research_source.py`       |
| bioRxiv / medRxiv feeds          | `app/data/seed_data.py` (placeholders)|
| ClinicalTrials.gov integration   | `app/models/evidence.py` (nct_id)     |
| Vector search / RAG              | `app/services/ai_service.py`          |
| Biomedical knowledge graphs      | New `app/services/kg_service.py`      |
| Real-time notifications          | New `app/api/websocket.py`            |
| PostgreSQL                       | Change `DATABASE_URL` in `.env`       |
| Anthropic Claude                 | Extend `ai_service.py`                |

---

## Security Notes

- JWT tokens expire after 60 minutes (configurable)
- Passwords are bcrypt-hashed; never stored in plaintext
- API keys live in `backend/.env` — never sent to the frontend
- All routes require authentication (except `/api/auth/token`, `/health`, `/`)
- Input is validated by Pydantic on every request
- CORS is restricted to `ALLOWED_ORIGINS`
- `.env` is in `.gitignore` — never committed

---

## Disclaimer

> BioArbitrage is an experimental research intelligence tool built for demonstration purposes.
> Evidence scores are experimental research-prioritization heuristics — not clinical probabilities,
> peer-reviewed findings, or treatment recommendations.
> All demo data is clearly labelled simulated data.
> This platform must not be used for clinical decision-making, patient diagnosis, or treatment selection.
