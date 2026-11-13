# AI-Driven Automated Testing

**Portfolio category:** AI-Integrated Engineering  
**Stack:** Python, AST, contract planning, unittest subprocess  
**Stage:** Tested local engineering reference; cloud deployment not claimed.

## Problem and solution

This standalone implementation addresses key engineering concerns behind ai-driven automated testing: correctness, isolation, observability, fault handling and a maintainable test boundary. It provides runnable code rather than a concept-only notebook.

## Architecture

Python source -> branch/error/boundary test ideas -> trusted test runner -> gap summary.

See [architecture / design decisions](docs/architecture.md), [security model](docs/security.md), [operational runbook](docs/runbook.md), [testing notes](docs/testing.md), and [provenance](docs/provenance.md).

## Quick start (Python 3.12+)

```bash
cd projects/12-ai-automated-test-engineering
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python src/app.py
```

No environment variables, paid APIs, secrets or cloud accounts are needed for the local tests. The production target would need its own deployment, monitoring, IAM and real integration tests.

## Engineering focus

- Branch/path discovery.
- Subprocess timeouts.
- Quality gaps.
- No untrusted test execution.


## What this **does not** claim

Generates reviewable test plans, not synthesized executable AI tests; subprocess is not a security sandbox.

## Next production milestone

Add LLM-based suggested test generation in a sandbox and mutation/coverage-guided test ranking.

## Interview guidance

Discuss *design decisions and their limitations* rather than claiming production-scale numbers or work experience not supported by these files. See docs/provenance.md for the evidence boundary.
