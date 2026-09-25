# ER Recall

ER Recall is a hackathon prototype for emergency medical-history retrieval and AI-assisted record analysis.

## Purpose

ER Recall helps a clinician quickly retrieve the documented medical history of a registered prototype patient and ask questions about that patient's available records.

The system is designed around:

- Patient-scoped emergency record retrieval
- Phone-based WebAuthn/passkey identification
- Structured medical-history panels
- Source-document references
- Deterministic conflict detection
- Local RAG-based AI assistance
- Temporary session-scoped AI data
- Patient isolation and auditability

## Data Policy

ER Recall uses synthetic demonstration data only.

The prototype does not integrate with:

- Aadhaar / UIDAI
- ABDM
- Hospital systems
- External patient databases

## Technology

### Frontend

- Next.js
- TypeScript
- Tailwind CSS

### Backend

- FastAPI
- Python

### Database

- PostgreSQL 16
- pgvector

### AI

- Ollama
- Local LLM
- Local embedding model

## Development Principles

1. Follow `PRD.md` for product requirements.
2. Follow `ARCHITECTURE.md` for technical architecture.
3. Follow `IMPLEMENTATION_PLAN.md` for implementation order.
4. Inspect existing code before making changes.
5. Make the smallest clean change required.
6. Keep secrets and environment-specific configuration outside source code.
7. Run real tests and verification after implementation.
8. Do not expose patient data in logs.
9. Keep AI responses grounded in retrieved patient records.
10. Do not allow the AI to make diagnosis, treatment, or medication decisions.

## Local Development

Environment-specific configuration belongs in `.env`.

Use `.env.example` as the configuration template.

The local PostgreSQL database and other services must be configured through environment variables rather than hard-coded credentials or secrets.

## Project Status

ER Recall is being developed as a finite hackathon prototype.

The intended end state is:

**ER Recall v1 - COMPLETE / END**