# Design Proposal: Ticket Summarization & Routing Assistant (V1)

## 1) Goal and First Iteration Scope

### Problem to Solve in V1

Support teams receive high volumes of inbound tickets/emails that require manual triage. In the first production iteration, the system will:

**Take a single ticket/email text as input**

**Produce:**
- Short summary (2–5 sentences)
- Category (e.g., Billing, Bug, Access, Feature Request)
- Priority (Low/Med/High with rationale)
- Suggested queue/team (e.g., "Support L2", "Billing Ops", "Security")
- Confidence score + needs_human_review flag

**Return output as structured JSON for downstream integration**

### Primary Success Metrics (V1)

- ≥80% agreement with human triage on category/queue on a curated eval set
- Reduce triage handling time (e.g., time-to-route) without increasing misroutes

### Explicit Non-Goals (V1)

To keep scope small and production-realistic, V1 will not:

- Auto-reply to customers or take actions (read-only recommendation)
- Integrate directly with ServiceNow/Jira (output is JSON only)
- Fine-tune a model (prompting + structured output only)
- Guarantee multilingual support or perfect formatting in all edge cases
- Provide an end-user UI (CLI or internal API only)

---

## 2) High-Level Production Architecture

### Overview

Two main components: a stateless inference service and supporting platform controls.

### Flow

1. Client (internal tool, batch job, or webhook) sends ticket text + metadata to the service
2. Service validates input, applies safety checks, and calls an LLM endpoint
3. Service returns JSON output and emits metrics/logs (without sensitive content)

### Components

#### Ticket Triage API (Stateless)

**Responsibilities:**
- Validation
- Prompting
- LLM call
- JSON schema enforcement
- Confidence/threshold logic
- Observability

**Deployment:** Containerized service (e.g., Azure Container Apps / AKS) or serverless function (if latency/limits fit)

#### LLM Endpoint

Open-source LLM hosted internally (or managed LLM where allowed). The design supports either via an adapter layer.

#### Secrets & Config

- **Secrets in Key Vault:** API keys, endpoints
- **Non-secret config:** Environment variables / config files (per environment)

#### Observability

- Structured logs + metrics (latency, error rate, token usage estimate, request volume, needs_review rate)
- Tracing/correlation id propagated end-to-end
- (Optional) Storage: Store only outputs and minimal metadata if needed (never raw ticket text by default)
- Retention policies applied

### Minimal Deployment Model

One deployable artifact (container) with:
- `/health` endpoint (liveness/readiness)
- Config validation at startup
- Standard CI pipeline: lint/test/build/publish

---

## 3) Ownership Boundaries

### Data Science / Applied AI

- Prompt template(s) and JSON output schema definition
- Label taxonomy (categories, queues, priority definitions)
- Offline evaluation set ("golden tickets") + quality metrics (accuracy, confusion matrix, abstain rate)
- Iteration plan for prompt improvements and calibration of confidence thresholds

### AI DevOps / ML Engineering

- Service implementation (API/CLI), adapters for LLM providers, schema enforcement
- CI/CD pipeline, environment configs, versioning, reproducible builds
- Operationalization: monitoring dashboards, alerting, runbooks, deployment strategy (canary/blue-green)

### Platform / Security

- IAM policies, network controls, secret management standards
- Logging/retention policy and compliance requirements
- Approved compute/runtime images and dependency scanning
- Data governance: what data can be sent to LLM and under which controls

---

## 4) Key Risks and Mitigations

### Cost Risks

#### Risks
- Unbounded prompt size (very long emails/threads)
- High throughput causing runaway LLM spend
- Retry storms during partial outages

#### Mitigations
- Hard caps: max input length; truncate with clear indicator
- Max output tokens; enforce JSON schema size limits
- Rate limiting per caller/service account; quotas per team
- Caching for duplicate tickets (hash-based) where appropriate
- Backoff + jitter on retries; circuit breaker when LLM is degraded
- Budgets and alerts based on estimated token usage and request counts

### Security & Privacy Risks

#### Risks
- Tickets can contain PII/secrets (addresses, phone numbers, API keys)
- Data leakage via logs, traces, or prompt storage
- Prompt injection embedded in ticket text ("ignore instructions…")

#### Mitigations
- Default: do not log raw ticket text; log only metadata (length, hashes, routing outcome)
- Redaction before logging and (optionally) before model call (policy-dependent)
- Secrets exclusively via Key Vault; least-privilege managed identity
- Treat ticket content as untrusted: strong system instructions + strict JSON output + injection heuristics
- Private networking controls if using internal LLM; restrict egress where applicable
- Access control: only approved internal callers; audit logs for access

### Operational Risks

#### Risks
- Latency spikes; timeouts; flaky model availability
- Model/prompt changes causing regression
- Dependency drift and environment inconsistencies

#### Mitigations
- Timeouts and graceful fallback: return "needs_human_review=true" with partial results
- Version prompts and schemas; release with canary and rollback
- Continuous evaluation in CI using the golden set (regression checks)
- Pinned dependencies; container builds; automated vulnerability scanning
- SLOs and alerts: error rate, p95 latency, abstain rate, misroute indicators

---

## 5) Trade-Offs and Decisions (V1)

- **Recommendation-only vs auto-action:** V1 outputs suggestions only. This reduces harm from misroutes and supports safe adoption.

- **Simple taxonomy:** Fixed categories/queues reduces complexity and improves evaluation.

- **No ticket storage by default:** Minimizes privacy risk; enables compliance-friendly rollout.

- **Provider abstraction:** Slight extra engineering, but prevents lock-in and makes open-source vs managed LLM a deploy-time choice.

---

## 6) Next Steps After V1 (Planned V2+)

- Add optional integration (ServiceNow/Jira) behind feature flag
- Add "similar historical tickets" retrieval (lightweight RAG) for better accuracy
- Add per-queue routing policies and role-based access controls if multiple departments use it
- Improve safety: richer PII detection, policy-based redaction, and monitored injection patterns
- Add human feedback loop (approve/correct routing) to improve taxonomy and evaluation
