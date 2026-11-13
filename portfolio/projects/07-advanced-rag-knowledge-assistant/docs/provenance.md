# Portfolio provenance and claims

This project is newly authored portfolio reference code, independent of any employer source or private production service.

**What exists:** Document -> overlapping chunk -> tenant-scoped BM25 -> retrieved excerpts -> optional generator -> source checks; tests in `tests/test_app.py`.

**What remains:** Add hybrid vectors, durable vector index, authz gateway, LLM adapter, safety evaluations and prompt-injection testing.

**Limitations:** Offline lexical search and optional generation interface; no remote LLM or embedding provider configured.

Do not describe this project as a four- or five-year production deployment or claim measured users, performance, uptime, savings, AI accuracy, or business outcomes without independently collecting data.
