# HackRadar AI

An intelligent, agentic AI-powered platform designed to discover, extract, verify and recommend hackathons, coding competitions, AI challenges and technology opportunities.

## Overview

HackRadar AI aims to simplify opportunity discovery by bringing relevant technology events into a centralized platform. The system is designed to automatically collect event information, prevent duplicates, evaluate eligibility and provide personalized recommendations.

## Current Features

- Modular full-stack architecture
- FastAPI REST API
- Next.js frontend
- PostgreSQL database
- SQLAlchemy ORM
- Alembic database migrations
- Extensible discovery adapter architecture
- AtCoder and Codeforces discovery adapters
- Secure RSS parsing and initial Hack Club adapter
- Deterministic event extraction
- Event normalization
- Duplicate prevention
- Persistent ingestion pipeline
- Discovery execution history
- Source health monitoring
- Extraction provenance tracking
- Database transaction management
- Isolated integration testing
- 194 passing automated tests

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| HTTP Client | HTTPX |
| Content Parsing | BeautifulSoup, lxml |
| Validation | Pydantic |
| Testing | Pytest |
| Infrastructure | Docker, Docker Compose |

## System Architecture

```text
Discovery Sources
       |
Discovery Orchestrator
       |
Source Adapters
       |
Event Extraction
       |
Normalization and Deduplication
       |
PostgreSQL Database
       |
FastAPI REST API
       |
Next.js Frontend
```

## Project Structure

```text
hackradar-ai/
├── apps/
│   ├── api/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   ├── core/
│   │   │   ├── db/
│   │   │   ├── discovery/
│   │   │   ├── extraction/
│   │   │   ├── models/
│   │   │   ├── repositories/
│   │   │   ├── schemas/
│   │   │   └── services/
│   │   ├── tests/
│   │   └── requirements.txt
│   └── web/
├── alembic/
├── docs/
├── compose.yaml
├── alembic.ini
├── .env.example
├── .gitignore
└── README.md
```

## Local Development

### Prerequisites

- Python 3.11
- Node.js and npm
- Docker and Docker Compose
- Git

### Database Setup

Create a local `.env` file using `.env.example` as a template and configure secure database credentials.

```bash
docker compose up -d db
```

### Backend Setup

From the project root:

```bash
cd apps/api
python -m venv .venv
```

Activate the virtual environment and install the dependencies:

```bash
pip install -r requirements.txt
```

From the project root, apply database migrations using the backend virtual environment:

```bash
alembic upgrade head
```

From `apps/api`, start the backend:

```bash
python -m uvicorn app.main:app --reload
```

Backend API: http://localhost:8000

API documentation: http://localhost:8000/docs

### Frontend Setup

```bash
cd apps/web
npm ci
npm run dev
```

Frontend: http://localhost:3000

### Testing

Configure a separate test database and apply its migrations before running integration tests.

From the project root:

```bash
alembic -x target=test upgrade head
```

From `apps/api`:

```bash
python -m pytest -q
```

Latest verified development result:

```text
194 passed, 1 warning
No broken requirements found.
```

## Development Roadmap

- [x] Full-stack project foundation
- [x] PostgreSQL database architecture
- [x] Database migrations
- [x] REST API implementation
- [x] Discovery orchestration
- [x] Initial discovery adapters
- [x] Deterministic event extraction
- [x] Persistent ingestion pipeline
- [x] Exact duplicate prevention
- [x] RSS parser implementation
- [ ] Complete RSS adapter integration
- [ ] Expanded hackathon discovery
- [ ] AI-powered event extraction
- [ ] Event verification
- [ ] Advanced cross-platform deduplication
- [ ] Eligibility evaluation
- [ ] Personalized recommendations
- [ ] Real-data frontend integration
- [ ] Autonomous discovery agent
- [ ] Scheduled discovery and notifications
- [ ] Authentication and user accounts
- [ ] Production deployment

## Responsible Data Collection

HackRadar AI is designed to use permitted public sources, official APIs and published feeds. Source permissions must be reviewed before enabling automated persistent collection.

Unknown event information is preserved as unknown rather than fabricated.

## Project Status

Under active development.

The backend foundation and initial discovery pipeline have passed automated verification. Live persistent discovery, AI-powered verification, personalized recommendations and autonomous scheduling are still under development.