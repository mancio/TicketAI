# TicketAI Project Structure & Quick Reference

## Project Overview

**TicketAI** is a production-ready ticket triage service that uses LLMs to summarize, categorize, prioritize, and route support tickets. Built for Azure deployment with focus on security, cost controls, and operational safety.

## Directory Structure

```
TicketAI/
├── src/                           # Application code
│   └── app/
│       ├── __init__.py           # Package marker
│       ├── main.py               # CLI entry point
│       ├── config.py             # Config loading + validation
│       ├── logging_setup.py       # Structured logs + PII redaction
│       ├── llm_client.py          # LLM abstraction (timeout, retry, circuit breaker)
│       └── pipeline.py            # Triage pipeline (validation, prompt, parsing)
│
├── tests/                          # Test suite
│   ├── __init__.py
│   └── test_smoke.py              # Smoke tests (config, validation, E2E)
│
├── .github/
│   └── workflows/
│       └── ci-cd.yml              # GitHub Actions CI/CD pipeline
│
├── README.md                       # Project overview + quick start
├── DESIGN.md                       # Architecture & design doc
├── REFLECTION.md                   # Implementation lessons learned
├── AZURE_DEPLOYMENT.md            # Azure setup guide (ACR, Container Apps, Key Vault)
├── RUNBOOK.md                      # Production on-call runbook
├── Dockerfile                      # Docker container config
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── .gitignore                      # Git ignore rules
├── .editorconfig                   # Editor formatting rules
└── sample_ticket.txt               # Example ticket for testing
```

## Getting Started (5 Minutes)

### 1. Setup
```bash
git clone https://github.com/yourusername/TicketAI.git
cd TicketAI
pip install -r requirements.txt
```

### 2. Run Tests
```bash
python -m tests.test_smoke
```

Expected output:
```
==============================================================
  TICKET TRIAGE SERVICE - SMOKE TESTS
==============================================================

✓ Testing config loading...
  ✓ Config loaded successfully
✓ Testing logging setup...
  ✓ Logger initialized, request_id: a1b2c3d4
... (6 more tests)

✓ ALL TESTS PASSED
```

### 3. Process a Ticket (Mock Mode)
```bash
python -m app.main --file sample_ticket.txt --output pretty
```

Example output:
```json
{
  "request_id": "x1y2z3w4",
  "summary": "Customer unable to access billing page after update.",
  "category": "Bug",
  "priority": "High",
  "queue": "Support L2",
  "confidence": 0.92,
  "needs_human_review": false,
  "metadata": {
    "input_length": 487,
    "latency_ms": 100,
    "tokens_estimate": 145,
    "success": true
  }
}
```

## Key Features

### ✅ Security
- **PII Redaction** — emails, phones, API keys, credit cards auto-redacted
- **Prompt Injection Protection** — ticket content treated as untrusted data
- **Secret Management** — API keys in Azure Key Vault only
- **Access Control** — least-privilege managed identity

### ✅ Cost Controls
- **Input limits** — max 5000 chars per ticket (configurable)
- **Rate limiting** — 60 req/min per caller (configurable)
- **Token tracking** — estimate usage per request
- **Circuit breaker** — auto-pause on LLM failures

### ✅ Reliability
- **Retries with backoff** — 2 retries with exponential backoff (1s, 2s)
- **Timeouts** — 30s default, configurable
- **Structured logging** — request tracing, latency tracking
- **Graceful degradation** — returns needs_human_review=true on errors

### ✅ Production Ready
- **Health endpoint** — `/health` for liveness/readiness checks
- **Docker support** — containerized for Azure Container Apps
- **CI/CD pipeline** — GitHub Actions with lint, test, build, deploy
- **Monitoring hooks** — logs, metrics, alerts (Azure Log Analytics)

## Configuration (Environment Variables)

| Variable | Default | Purpose |
|----------|---------|---------|
| `MODEL_NAME` | gpt-4 | LLM model to use |
| `LLM_ENDPOINT` | openai.com | LLM API endpoint |
| `LLM_API_KEY` | (required) | API key (in Key Vault!) |
| `MAX_INPUT_LENGTH` | 5000 | Max ticket chars |
| `MAX_OUTPUT_TOKENS` | 500 | Max response tokens |
| `TIMEOUT_SECONDS` | 30 | LLM timeout |
| `MAX_RETRIES` | 2 | Retry attempts |
| `RATE_LIMIT_PER_MINUTE` | 60 | Requests/min |
| `LOG_LEVEL` | INFO | DEBUG/INFO/WARNING/ERROR |
| `LOG_RAW_TICKET` | false | Log raw ticket? (privacy!) |
| `ENVIRONMENT` | development | dev/staging/production |
| `KEYVAULT_NAME` | (optional) | Azure Key Vault name |

Copy `.env.example` to `.env` and customize.

## Output Schema

```json
{
  "request_id": "string (for tracing)",
  "summary": "string (2-5 sentences)",
  "category": "Billing|Bug|Access|Feature Request|General",
  "priority": "Low|Medium|High",
  "queue": "Support L1|Support L2|Billing Ops|Security|Engineering",
  "confidence": 0.0-1.0,
  "needs_human_review": boolean,
  "metadata": {
    "input_length": int,
    "latency_ms": int,
    "tokens_estimate": int,
    "success": boolean
  }
}
```

## Core Components

### config.py
Loads and validates settings from environment variables. Validates at startup (e.g., MODEL_NAME required, timeouts >= 5s).

### logging_setup.py
Structured JSON logging with automatic PII redaction. Redacts:
- Emails (john@example.com)
- Phone numbers ((555) 123-4567)
- API keys (sk-...)
- Credit cards (1234-5678-...)

### llm_client.py
LLM abstraction layer with:
- Timeout enforcement
- Exponential backoff retries
- Circuit breaker (auto-pause after 5 failures)
- Mock mode for testing (no API key needed)

### pipeline.py
Orchestrates end-to-end triage:
1. Input validation (length, format)
2. Prompt preparation (injection-safe)
3. LLM call via client
4. Output parsing & schema validation
5. Taxonomy enforcement (fallback to defaults if invalid)

### main.py
CLI entry point. Usage:
```bash
python -m app.main --file tickets.txt
python -m app.main --text "Customer issue here"
python -m app.main --text "..." --output pretty
```

## Testing

### Run All Tests
```bash
python -m tests.test_smoke
```

### Tests Included
1. **config_loading** — Validates settings load
2. **logging_setup** — Logger initialization
3. **input_validation** — Rejects empty/oversized input
4. **output_validation** — Schema enforcement, fallbacks
5. **circuit_breaker** — Resilience logic
6. **mock_llm_call** — Works offline (no API key)
7. **end_to_end_pipeline** — Full triage flow

## Deployment

### Local Development
```bash
pip install -r requirements.txt
python -m app.main --text "test ticket" --output pretty
```

### Docker (Local)
```bash
docker build -t ticketai:latest .
docker run -e MODEL_NAME=gpt-4 -e LLM_API_KEY=sk-... ticketai:latest
```

### Azure Container Apps (Production)
See [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md) for complete guide.

```bash
# Quick version:
az containerapp create \
  --name ticketai-api \
  --resource-group my-rg \
  --image ticketai:latest \
  --env-vars MODEL_NAME=gpt-4 ...
```

## Monitoring & Alerts

### Key Metrics
- **latency_ms** — Time to triage ticket
- **tokens_estimate** — Token usage per request
- **error_rate** — % of failed requests
- **needs_review_rate** — % flagged for human review
- **misroute_rate** — % of incorrect categories/queues

### Alerts (Example)
- Error rate > 5% → Page on-call
- Token budget exceeded → Notify ML Eng
- Circuit breaker open > 5 min → Page on-call
- Misroute rate > 10% → Notify Data Science

See [RUNBOOK.md](RUNBOOK.md) for on-call procedures.

## Next Steps (After V1)

- [ ] Connect to real LLM (Azure OpenAI or open-source)
- [ ] Add ServiceNow/Jira integration (feature-flagged)
- [ ] Implement RAG with historical tickets
- [ ] Add per-queue routing policies
- [ ] Setup human feedback loop (approve/correct)
- [ ] Build analytics dashboard

## Files to Read First

1. **README.md** — Overview & quick start
2. **DESIGN.md** — Architecture & design decisions
3. **src/app/main.py** — Entry point (read to understand flow)
4. **tests/test_smoke.py** — Example usage patterns
5. **AZURE_DEPLOYMENT.md** — How to deploy to Azure
6. **REFLECTION.md** — Philosophy & lessons learned

## Troubleshooting

### ImportError: No module named 'app'
```bash
# Make sure you're in the project root
cd /path/to/TicketAI
python -m app.main --text "test"
```

### Config validation failed
```bash
# Check .env file
cat .env

# Or use defaults
python -m app.main --text "test"  # Uses defaults, works in mock mode
```

### Tests fail with "AssertionError"
```bash
# Check Python version (need 3.9+)
python --version

# Reinstall dependencies
pip install -r requirements.txt

# Run with debug
python -m tests.test_smoke  # Check output for specific failure
```

## Support

- **Issues**: Create GitHub issue
- **Questions**: See [DESIGN.md](DESIGN.md) for rationale
- **Deployment help**: See [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md)
- **On-call support**: See [RUNBOOK.md](RUNBOOK.md)

---

**Ready to deploy? Start with [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md).**
