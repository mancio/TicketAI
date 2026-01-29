# TicketAI Operational Runbook

## Overview

This runbook covers on-call procedures for the Ticket Triage service in production.

## Service Health

### Health Check Endpoint
```bash
curl https://your-app-url/health
```

Expected response:
```json
{
  "status": "healthy",
  "model": "gpt-4",
  "uptime_seconds": 86400
}
```

## Common Alerts & Responses

### Alert: Circuit Breaker Open (LLM Down)

**Detection:** Circuit breaker has tripped (5+ consecutive LLM failures)

**Response:**
```bash
# 1. Check LLM service status
curl https://api.openai.com/v1/models -H "Authorization: Bearer $LLM_API_KEY"

# 2. Verify credentials in Key Vault
az keyvault secret show --vault-name ticketai-kv --name llm-api-key

# 3. Check service logs
az containerapp logs show --name ticketai-api --resource-group ticketai-rg

# 4. If LLM is down, system auto-returns needs_human_review=true
#    No action needed; users see "needs review" flag

# 5. Once LLM recovers, circuit breaker auto-resets after 60 seconds
```

**SLA:** If LLM is down > 30 min, page on-call engineer

### Alert: High Error Rate (> 5%)

**Detection:** Error rate exceeds threshold

**Response:**
```bash
# 1. Check recent logs
az containerapp logs show \
  --name ticketai-api \
  --resource-group ticketai-rg \
  --follow

# 2. Look for patterns:
#    - JSON parse errors → LLM output changed
#    - Timeout errors → LLM slow or network issue
#    - Input validation errors → Spam/abuse?

# 3. If LLM output schema changed, escalate to Data Science team

# 4. If timeout-heavy, check:
TIMEOUT_SECONDS=$(az containerapp show \
  --name ticketai-api \
  --resource-group ticketai-rg \
  --query "properties.template.containers[0].env[?name=='TIMEOUT_SECONDS'].value" -o tsv)

# 5. If needed, roll back to previous image:
az containerapp update \
  --name ticketai-api \
  --resource-group ticketai-rg \
  --image <previous-image-sha>
```

### Alert: High Token Usage (> Budget)

**Detection:** Estimated daily token spend exceeds threshold

**Response:**
```bash
# 1. Check token metrics in last 1 hour
az monitor metrics list \
  --resource /subscriptions/{id}/resourceGroups/ticketai-rg/providers/Microsoft.App/containerApps/ticketai-api \
  --metric "tokens_estimate" \
  --start-time 2024-01-29T00:00:00Z \
  --end-time 2024-01-29T01:00:00Z

# 2. If spike detected, check for:
#    - Unusually long tickets (truncate?)
#    - Rate-limit bypass (check for spam)
#    - Model change (gpt-4 is more expensive)

# 3. Options:
#    a) Lower MAX_INPUT_LENGTH temporarily
az containerapp update \
  --name ticketai-api \
  --resource-group ticketai-rg \
  --set-env-vars MAX_INPUT_LENGTH=3000

#    b) Enable caching (hash-based duplicate detection)
#    c) Escalate to leadership if budget exceeded
```

### Alert: High Misroute Rate (> 10%)

**Detection:** More tickets being flagged needs_human_review than expected

**Response:**
```bash
# 1. This usually means model confidence dropped
# 2. Check recent tickets flagged for review:
az logs query \
  -w /subscriptions/{id}/resourcegroups/ticketai-rg/providers/microsoft.insights/components/ticketai \
  "customEvents | where name == 'needs_human_review' | order by timestamp desc | take 20"

# 3. Patterns to look for:
#    - New ticket type (e.g., complaints about X)
#    - Prompt drift (LLM not following instructions)
#    - Language change

# 4. If prompt-related, escalate to Data Science:
#    - Review last 5 misroutes
#    - Test prompt with golden eval set
#    - A/B test new prompt on 10% traffic (canary)

# 5. If broader issue, consider rollback:
az containerapp update \
  --name ticketai-api \
  --resource-group ticketai-rg \
  --image <previous-image-sha>
```

## Manual Remediation

### Restart Service
```bash
az containerapp update \
  --name ticketai-api \
  --resource-group ticketai-rg \
  --no-wait

# Wait 30 seconds, then verify
sleep 30
curl https://ticketai-api.azurecontainerapps.io/health
```

### Scale Down (Maintenance)
```bash
az containerapp update \
  --name ticketai-api \
  --resource-group ticketai-rg \
  --min-replicas 0
```

### Scale Up
```bash
az containerapp update \
  --name ticketai-api \
  --resource-group ticketai-rg \
  --min-replicas 1 \
  --max-replicas 10
```

### Update Configuration (No Redeploy)
```bash
az containerapp update \
  --name ticketai-api \
  --resource-group ticketai-rg \
  --set-env-vars \
    LOG_LEVEL=DEBUG \
    MAX_INPUT_LENGTH=4000 \
    TIMEOUT_SECONDS=45
```

## Debugging

### Enable Debug Logs
```bash
az containerapp update \
  --name ticketai-api \
  --resource-group ticketai-rg \
  --set-env-vars LOG_LEVEL=DEBUG
```

### Tail Logs
```bash
az containerapp logs show \
  --name ticketai-api \
  --resource-group ticketai-rg \
  --follow
```

### Test Locally (Offline)
```bash
# Clone repo
git clone https://github.com/your-org/TicketAI.git
cd TicketAI

# Install deps
pip install -r requirements.txt

# Run with mock (no API key needed)
python -m app.main --text "test ticket content" --output pretty
```

## Escalation Path

| Severity | Response Time | Escalate To |
|----------|---------------|-------------|
| **Critical** (error rate > 10%, outage) | 5 min | On-call + Engineering Lead |
| **High** (error rate 5-10%, token spike) | 15 min | ML Engineering Lead |
| **Medium** (misroute spike, latency > 5s) | 1 hour | Data Science + ML Engineering |
| **Low** (occasional errors, warnings) | Next business day | Team Slack channel |

## Contact Info

- **ML Engineering Lead:** @alice-ml-eng
- **Data Science Lead:** @bob-data-science
- **Platform/Security:** @charlie-platform
- **On-Call Rotation:** PagerDuty (ticketai-oncall)

## Post-Incident Checklist

After resolving any production incident:

- [ ] Root cause identified
- [ ] Fix tested locally
- [ ] Deployment rolled out
- [ ] Monitoring confirms resolution
- [ ] Post-mortem scheduled (if P1)
- [ ] Runbook updated (if process gap found)
- [ ] Team notified of learnings
