# DONS — DigitalOcean Native Stack

AI-powered cloud migration and store intelligence platform for SMBs. Migrate AWS infrastructure to DigitalOcean with autonomous agents, and query your product catalog using RAG-powered AI.

## What It Does

1. **Upload** your AWS Terraform files (.tf, .tf.json)
2. **Analyze** infrastructure — get a migration plan, risk analysis, and cost comparison
3. **Deploy** auto-generated DigitalOcean Terraform with one click via the DO API
4. **Ask questions** about your products using a pre-built DigitalOcean Knowledge Base (OpenSearch) and Gradient AI

## AI Agents

| Agent | Role | Tech |
|-------|------|------|
| 🏗️ Migration Architect | Analyzes AWS infra, generates migration plans with risk analysis | Gradient AI (llama3-8b-instruct) |
| ⚙️ DevOps Agent | Generates Terraform, deploys infrastructure, monitors resources | DO API v2 |
| 🤖 AI Enablement | Recommends AI/ML capabilities on DigitalOcean | Gradient AI |
| 🧠 Store Intelligence | RAG-powered product Q&A via DO Knowledge Base (OpenSearch) | Gradient AI + DO KB |

## Tech Stack

- **UI**: Streamlit (Python)
- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL (DO Managed) / SQLite for local dev
- **AI Inference**: DigitalOcean Gradient AI (llama3-8b-instruct)
- **Knowledge Base**: DigitalOcean Knowledge Base (OpenSearch) — created in DO portal
- **Storage**: DigitalOcean Spaces (S3-compatible)
- **Deployment**: DigitalOcean API v2 (Droplets, Managed DB, Spaces, Load Balancers)

## Quick Start

### 1. Set up environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 2. Start the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start the Streamlit UI

```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

### 4. Open the app

- Streamlit UI: http://localhost:8501
- Backend API docs: http://localhost:8000/docs

## Environment Variables

See `.env.example` for all required variables. Key ones:

| Variable | Description |
|----------|-------------|
| `DIGITALOCEAN_API_TOKEN` | DigitalOcean API token |
| `GRADIENT_AI_MODEL_KEY` | Gradient AI API key |
| `SPACES_ACCESS_KEY_ID` | DO Spaces access key |
| `SPACES_ACCESS_KEY` | DO Spaces secret key |
| `DO_KB_ENDPOINT` | Knowledge Base retrieve endpoint |
| `DATABASE_URL` | PostgreSQL connection string (or `sqlite:///./dons_local.db` for local) |

## Store Intelligence — Knowledge Base Setup

The Store Intelligence agent uses a pre-created DigitalOcean Knowledge Base (OpenSearch). To set it up:

1. Go to the DigitalOcean portal → GenAI Platform → Knowledge Bases
2. Create a Knowledge Base and upload your product documents (PDFs, CSVs, etc.)
3. Copy the KB retrieve endpoint and set it as `DO_KB_ENDPOINT` in `.env`

The app will query this KB for semantic + lexical hybrid search and generate answers via Gradient AI.

## Sample Files

The `samples/` directory contains test infrastructure files:

- `ecommerce_aws.tf` — Sample AWS Terraform with EC2, RDS, S3, ALB
- `ecommerce_aws.tf.json` — Same infrastructure in Terraform JSON format

All resources map to DigitalOcean equivalents (Droplets, Managed DB, Spaces, Load Balancer).

## API Endpoints

### Migration
- `POST /api/upload` — Upload infrastructure files
- `POST /api/analyze` — Parse and analyze infrastructure
- `POST /api/escape-plan` — Generate migration plan
- `POST /api/cost` — Calculate cost comparison
- `POST /api/generate-terraform` — Generate DO Terraform
- `POST /api/deploy` — Deploy to DigitalOcean
- `POST /api/destroy` — Tear down deployed resources

### Store Intelligence
- `POST /api/intelligence/ask` — Ask questions (RAG via DO Knowledge Base)

### Health
- `GET /health` — Backend health check

## Project Structure

```
dons/
├── backend/                    # FastAPI backend
│   ├── main.py                # API endpoints
│   ├── models.py              # SQLAlchemy models
│   ├── schemas.py             # Pydantic schemas
│   ├── database.py            # DB connection
│   ├── terraform_parser.py    # Parse .tf / .json / .yaml
│   ├── migration_mapper.py    # AWS → DO resource mapping
│   ├── cost_estimator.py      # Cost comparison
│   ├── terraform_generator.py # Generate DO Terraform
│   ├── do_deployer.py         # Deploy via DO API
│   ├── cloud_migration_architect.py  # Migration Architect agent
│   ├── devops_agent.py        # DevOps agent
│   ├── ai_enablement_agent.py # AI Enablement agent
│   └── store_intelligence_agent.py   # Store Intelligence agent (DO KB)
├── streamlit_app/             # Streamlit UI
│   ├── app.py                 # Main entry point
│   ├── api_client.py          # Backend API client
│   ├── config.py              # Configuration
│   ├── components/            # Sidebar, agent activity feed
│   └── views/                 # Migration & Intelligence views
│       ├── home.py
│       ├── migration/         # Upload, Summary, Deployment
│       └── intelligence/      # Ask Your Products (chat)
├── samples/                   # Sample AWS Terraform files
├── .do/app.yaml               # DigitalOcean App Platform spec
├── docker-compose.yml         # Local dev with Docker
└── README.md
```

## Deployment to DigitalOcean

The app is configured for DO App Platform via `.do/app.yaml`:

- **backend** — FastAPI service (port 8000)
- **streamlit** — Streamlit UI (port 8501, routes to `/`)
- **db** — Managed PostgreSQL

Push to your repo and connect it in the DO App Platform dashboard.

## License

MIT
