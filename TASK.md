# TicketAI Technical Challenge – Task Description

## Overview

**Goal:** Assess how to approach productizing AI, making trade-offs, and thinking about cost, security, and operations.

---

## Context

You join a team where Data Scientists have delivered a working notebook using an open-source LLM / embeddings.

It works locally, but it is **not production-ready**:
- No cost control
- No clear deployment model
- No security or misuse considerations
- No clear ownership boundaries

**Your task:** Define and demonstrate how this could realistically move toward production.

---

## Part 1 – Design (most important)

Prepare a short design proposal (max 1–2 pages) covering:

1. **What problem you would solve in the first iteration** (and what you explicitly would not)
2. **High-level production architecture**
3. **Ownership boundaries** (DS vs AI DevOps vs platform)
4. **Key risks** (cost, security, operations) and how you would mitigate them

---

## Part 2 – Minimal Implementation

Implement one of the following (your choice):

1. **A production-ready skeleton** (repo / workspace structure, config, logging, entrypoint), OR
2. **Hardening of a simple AI notebook** (parameterization, config separation, readiness for CI/CD)

**Important:** A fully working model or UI is not required.

---

## Part 3 – Security & Misuse (short, written)

Briefly describe:

1. **3 realistic ways this system could be misused or cause problems**
2. **How you would mitigate them in practice**

---

## Part 4 – Reflection (1 short paragraph)

Which parts of this task cannot realistically be solved by relying on AI tools alone, and why?

---

## What to Submit

- Repository / Databricks workspace / notebook
- Short written description (design + decisions + trade-offs)

---

## Key Principle

This task is intentionally scoped to evaluate **decision-making and production thinking**, not volume of code.
