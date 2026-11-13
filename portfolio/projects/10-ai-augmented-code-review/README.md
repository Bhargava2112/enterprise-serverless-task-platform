# AI-Augmented CI/CD Code Review

**Portfolio category:** AI-Integrated Engineering  
**Stack:** Python, AST, diff parser, secret and risk rules  
**Stage:** Tested local engineering reference; cloud deployment not claimed.

## Problem and solution

This standalone implementation addresses key engineering concerns behind ai-augmented ci/cd code review: correctness, isolation, observability, fault handling and a maintainable test boundary. It provides runnable code rather than a concept-only notebook.

## Architecture

Changed lines -> deterministic policy scanner -> findings with line numbers -> CI gate -> optional advisory model.

See [architecture / design decisions](docs/architecture.md), [security model](docs/security.md), [operational runbook](docs/runbook.md), [testing notes](docs/testing.md), and [provenance](docs/provenance.md).

## Quick start (Python 3.12+)

```bash
cd projects/10-ai-augmented-code-review
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python src/app.py
```

No environment variables, paid APIs, secrets or cloud accounts are needed for the local tests. The production target would need its own deployment, monitoring, IAM and real integration tests.

## Engineering focus

- Critical secret detection.
- Python ast checks.
- Diff line mapping.
- Severity gates.


## What this **does not** claim

Deterministic static analysis; no hosted AI provider configured; false positives require review.

## Next production milestone

Add GitHub PR review integration, SARIF, risk prioritization, secret vault redaction and LLM advisory.

## Interview guidance

Discuss *design decisions and their limitations* rather than claiming production-scale numbers or work experience not supported by these files. See docs/provenance.md for the evidence boundary.
