# TicketAI (Minimal Skeleton)

## Problem statement
Support teams receive high volumes of tickets that require manual triage. This minimal skeleton demonstrates how a production service would be structured (config, logging, entrypoint) without building a full model or UI.

## What this is
A **production-ready skeleton**: config separation, structured logging, and a CLI entrypoint that returns stubbed JSON.

## What is intentionally missing
- Real LLM calls
- UI or integrations
- Tests, Docker, CI/CD (listed as next steps)

## How to run locally
```bash
pip install -r requirements.txt
python -m app.main --text "Customer cannot log in"
```

## Required env vars (example)
```bash
ENVIRONMENT=development
LOG_LEVEL=INFO
MAX_INPUT_LENGTH=5000
```

## What’s stubbed
The pipeline returns fixed JSON values and does not call any model. This keeps scope minimal and focused on structure.

## Trade-offs
- ✅ Fast to review, clear scope
- ❌ Not production-complete (no model, no API)

## Next steps
- Add tests
- Add Dockerfile and CI/CD
- Implement real model call + schema validation

See DESIGN.md for the full Part 1 design.
