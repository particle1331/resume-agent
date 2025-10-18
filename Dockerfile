FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /opt
COPY . .
RUN uv sync --frozen --no-dev

EXPOSE 8080

CMD ["uv", "run", "python", "-m", "app.main"]
