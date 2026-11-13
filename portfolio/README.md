# Engineering Portfolio — 14 Standalone Reference Projects

Fourteen independently runnable, **locally tested** engineering references spanning AWS, Azure/ML, generative AI, AI-assisted development, and database systems. Each subproject has its own source code, tests, Dockerfile, Makefile, architecture, security, operations, and provenance documentation.

**This collection belongs alongside Project 01, the standalone Enterprise Serverless Task Management Platform already present in this repository.**

## Directory index

| ID | Project | Category |
|---|---|---|
| 02 | [Real-Time Retail Data Processing Platform](projects/02-real-time-retail-pipeline/README.md) | AWS / Data Engineering |
| 03 | [Cloud-Native Microservices Reliability Platform](projects/03-microservices-reliability/README.md) | AWS / Distributed Systems |
| 04 | [Enterprise MLOps Platform](projects/04-enterprise-mlops/README.md) | Azure / Machine Learning |
| 05 | [Intelligent Enterprise Data Lakehouse](projects/05-enterprise-lakehouse/README.md) | Azure / Data Engineering |
| 06 | [AI-Powered Manufacturing Quality Inspection](projects/06-manufacturing-quality-inspection/README.md) | Azure / Applied ML |
| 07 | [Advanced RAG Enterprise Knowledge Assistant](projects/07-advanced-rag-knowledge-assistant/README.md) | Generative AI / LLM |
| 08 | [Multi-Agent Software Engineering Assistant](projects/08-multi-agent-software-engineer/README.md) | Generative AI / Agents |
| 09 | [Natural Language to SQL Analytics Engine](projects/09-natural-language-sql-analytics/README.md) | Generative AI / Data |
| 10 | [AI-Augmented CI/CD Code Review](projects/10-ai-augmented-code-review/README.md) | AI-Integrated Engineering |
| 11 | [AI-Powered Incident Root Cause Analysis](projects/11-ai-incident-root-cause/README.md) | AI-Integrated Engineering |
| 12 | [AI-Driven Automated Testing](projects/12-ai-automated-test-engineering/README.md) | AI-Integrated Engineering |
| 13 | [PostgreSQL Transaction Engine](projects/13-postgresql-transaction-engine/README.md) | Database Engineering |
| 14 | [Change Data Capture / Replication System](projects/14-change-data-capture-replication/README.md) | Database Engineering |
| 15 | [Enterprise Data Warehouse / Incremental ETL](projects/15-incremental-enterprise-warehouse/README.md) | Database Engineering |


## Run everything

```bash
python scripts/test_all.py
```

Requires Python 3.12+; the suite uses only the standard library and synthetic fixtures. To run a specific project:

```bash
cd projects/07-advanced-rag-knowledge-assistant
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Engineering integrity

These are newly built portfolio projects, not real multi-year employer engagements. AWS/Azure deployments, hosted language models, cloud infrastructure integrations and production performance claims are **not** represented as complete. Provider targets are documented as extension plans. Each project is labeled with its implementation boundary.

All source material is self-contained; no secrets or customer data are required.
