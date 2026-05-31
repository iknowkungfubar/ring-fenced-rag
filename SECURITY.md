# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅ Yes |

## Reporting a Vulnerability

Ring-Fenced RAG takes security seriously. If you discover a security vulnerability, please report it via **GitHub's private vulnerability reporting**:

1. Go to https://github.com/iknowkungfubar/ring-fenced-rag/security/advisories
2. Click "New draft security advisory"
3. Provide a clear description, reproduction steps, and impact assessment

Alternatively, email: turin.ortherion@gmail.com

**Please do NOT report security vulnerabilities via public GitHub issues.**

### Expected Response Times
- **Initial acknowledgment**: Within 48 hours
- **Triage / validation**: Within 5 business days
- **Fix timeline**: Dependent on severity (critical: 7 days, high: 14 days, medium: 30 days)

## Security Design Principles

Ring-Fenced RAG's architecture enforces security at the infrastructure level:

1. **Zero-trust retrieval**: Role-based access control is enforced via PostgreSQL JSONB `@>` containment operator at query time — not in application code. An attacker who bypasses the API still cannot retrieve unauthorized documents from the database directly.
2. **Zero egress by default**: All inference, embedding, and storage runs locally. No data reaches an external API unless the operator explicitly configures an external LLM.
3. **Idempotent ingestion**: LangChain SQLRecordManager tracks content hashes, preventing duplicate vectors and ensuring document updates propagate correctly.
4. **Redacted telemetry**: Trace redaction is enabled by default. Full traces expire after 7 days.
5. **API key authentication**: SHA-256 hashed keys with constant-time comparison. Keys map to roles, not users.

## Hall of Fame

We appreciate responsible disclosure. Contributors who report valid security vulnerabilities will be acknowledged here (with permission).
