FROM python:3.11-slim-bookworm

# Ensure all system packages are up to date and security patches are applied
WORKDIR /app
RUN apt-get update && \
	apt-get upgrade -y && \
	apt-get install --no-install-recommends -y ca-certificates && \
	apt-get clean && \
	rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY ./app ./app
COPY ./tests ./tests
RUN pytest --maxfail=1 --disable-warnings --tb=short
CMD ["sh", "-c", "pytest --maxfail=1 --disable-warnings --tb=short && uvicorn app.main:app --host 0.0.0.0 --port 3001"]
