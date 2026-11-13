# AI-Powered Manufacturing Quality Inspection

**Portfolio category:** Azure / Applied ML  
**Stack:** Python, grayscale images, connected components, logistic classifier  
**Stage:** Tested local engineering reference; cloud deployment not claimed.

## Problem and solution

This standalone implementation addresses key engineering concerns behind ai-powered manufacturing quality inspection: correctness, isolation, observability, fault handling and a maintainable test boundary. It provides runnable code rather than a concept-only notebook.

## Architecture

Camera/P2 PGM -> image validation -> feature extractor -> trainable classifier -> audit-ready inspection decision.

See [architecture / design decisions](docs/architecture.md), [security model](docs/security.md), [operational runbook](docs/runbook.md), [testing notes](docs/testing.md), and [provenance](docs/provenance.md).

## Quick start (Python 3.12+)

```bash
cd projects/06-manufacturing-quality-inspection
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python src/app.py
```

No environment variables, paid APIs, secrets or cloud accounts are needed for the local tests. The production target would need its own deployment, monitoring, IAM and real integration tests.

## Engineering focus

- Input bounds.
- Explainable features.
- Decision threshold and review zone.
- Model serialization.


## What this **does not** claim

Trainable visual baseline using P2 grayscale; not a validated production deep-learning vision model.

## Next production milestone

Collect labeled images, augment, evaluate production CV model, deploy on Azure IoT Edge or Azure ML.

## Interview guidance

Discuss *design decisions and their limitations* rather than claiming production-scale numbers or work experience not supported by these files. See docs/provenance.md for the evidence boundary.
