# Verification strategy

## Locally exercised in CI

- Repeatable Python unittest suite: `PYTHONPATH=src python -m unittest discover -s tests -v`.
- Covers normal operations and selected boundary, retry, access or failure scenarios.
- Dependencies: Python 3.12 standard library only.

## Not yet exercised

- Real cloud/provider integrations, IAM permissions, distributed network failures.
- Multi-process concurrency and chaos tests, sustained workloads, load/latency benchmarks.
- Full security assessment, end-to-end UX and production monitoring.

Keep these distinctions explicit in interviews or published documentation.
