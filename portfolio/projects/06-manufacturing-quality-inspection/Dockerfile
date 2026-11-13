FROM python:3.12-slim
WORKDIR /workspace
COPY src/ ./src/
COPY tests/ ./tests/
ENV PYTHONPATH=/workspace/src PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 65532:65532
CMD ["python", "-m", "unittest", "discover", "-s", "tests", "-v"]
