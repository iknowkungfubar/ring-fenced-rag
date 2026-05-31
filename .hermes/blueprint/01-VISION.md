# Product Vision: Ring-Fenced RAG (RFR)

## One-Liner
A self-hosted, zero-trust RAG system that lets you index internal documentation and query it via CLI, API, or web UI — with access control enforced at the database level, not the application layer.

## Elevator Pitch
Every organization has internal documentation trapped in Confluence, Notion, Jira, PDFs, and Markdown files. Cloud RAG services expose that proprietary IP to external APIs. Existing self-hosted RAG tools (PrivateGPT, GPT4All) lack production-grade access control — any user with access can query any document.

Ring-Fenced RAG solves this with a **zero-trust retrieval architecture**: documents are tagged with role-based ACL metadata at ingestion time, and the vector database **enforces** that metadata at query time via JSONB filters and SQL-level containment operators. A junior engineer literally cannot retrieve executive-only document chunks, because the database refuses the mathematical comparison.

The product ships as a single `pip install` + `docker compose up`, with sensible defaults but full configurability: choose your embedding model, LLM provider (vLLM/Ollama/LM Studio), document sources, and role scheme. Designed for DevOps teams, security-conscious orgs, and anyone who can't or won't send their IP to a third-party API.

## Target Users
- **Primary persona: DevOps / Platform Engineer** — Responsible for infrastructure documentation. Wants internal docs searchable without data leaving the network. Needs to restrict access to sensitive runbooks (production credentials, architecture decisions) by team role. Comfortable with CLI and Docker.
- **Secondary persona: IT Operations Manager** — Needs to deploy a team-wide documentation Q&A tool. Wants a web UI for non-technical team members. Cares about setup simplicity and user management.
- **Tertiary persona: Security-Conscious Knowledge Worker** — Has proprietary documentation they want to query with AI. Not deeply technical, but concerned about data privacy. Will use the web UI primarily.

## Core Goals
1. **Easy Install, Zero Leak** — Single command to install and deploy. All computation stays local by default. No data ever reaches an external API unless the operator explicitly configures an external LLM.
2. **Role-Based Ring-Fence** — Every document chunk carries `allowed_roles` metadata. The vector database enforces this at query time. Unauthorized queries return zero results — not sanitized results, zero results. The ring-fence is mathematically enforced, not politely requested.
3. **Idempotent Ingestion** — Ingest the same document 10 times, get exactly 1 copy. Document updates replace old vectors. Deletes remove them. The semantic space stays clean without manual cleanup.
4. **Pluggable Sources & Models** — Ingest from directories, Git repos, Confluence, Notion, or raw files. Choose any sentence-transformer embedding model. Use vLLM, Ollama, LM Studio, or OpenAI-compatible API for generation.
5. **Query Anywhere** — CLI for quick questions, Web UI for rich exploration, REST API for integration into existing tools (Slack bots, incident response, CI queries).

## Success Metrics
- **Time to first answer:** < 5 minutes from `pip install` to answering a question against local docs
- **Ingestion throughput:** > 100 pages/minute on a single CPU core (bge-small)
- **Query latency (p95):** < 2 seconds for retrieval + generation (with local LLM)
- **Auth breach surface:** 0 — no mechanism exists for a user to retrieve chunks they don't have role access to, even by crafting raw SQL
- **Install base target:** 100+ GitHub stars, 500+ `pip install`s within 6 months of v1.0 release

## Non-Goals (v1)
- Multi-organization tenancy (single-org per deployment)
- SSO/SAML integration (role-based API key auth only initially)
- Real-time document syncing (periodic/on-demand ingestion)
- Video/image embedding (text-only)
- Kubernetes operator (Docker Compose only — K8s helm chart is v2)
- Multi-modal RAG (text-only)
- Streaming UI responses (full response only in v1)

## Key Constraints
- **Timeline:** Working MVP in 4 weeks, v1.0 release in 8 weeks
- **Data privacy:** Zero data egress by default. All inference, embedding, and storage MUST run locally unless explicitly overridden.
- **Deployment:** Docker Compose as primary deployment method. Standalone Python mode for development/light use.
- **Compliance-ready:** Architecture must support future SOC2/GDPR audit trails
- **AMD GPU support:** Must work with ROCm (user has AMD hardware)
- **Python 3.13:** Target runtime
