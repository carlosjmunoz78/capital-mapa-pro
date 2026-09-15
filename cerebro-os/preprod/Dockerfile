FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace
COPY cerebro-os /workspace/cerebro-os

RUN useradd --create-home --uid 10001 cerebro
USER 10001:10001

CMD ["python", "cerebro-os/preprod/run_candidate.py"]
