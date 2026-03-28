FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /forge
COPY seed.py .
COPY core.md .
CMD ["python3", "-u", "seed.py"]
