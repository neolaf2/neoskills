FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY src/ src/

# Install dependencies
RUN uv sync --no-dev

# No credentials baked in - mount .env or pass env vars at runtime
# docker run -v /path/to/.env:/app/.env neoskills ...
# docker run -e ANTHROPIC_API_KEY=... neoskills ...

ENTRYPOINT ["uv", "run", "neoskills"]
CMD ["--help"]
