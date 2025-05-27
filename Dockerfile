FROM python:3.13-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates nodejs npm

ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /workspace

# Copy requirements first for better caching
COPY pyproject.toml .
RUN uv sync

# Copy the rest of the application
COPY . .

EXPOSE 8080
EXPOSE $PORT

CMD ["uv", "run", "main.py"]
