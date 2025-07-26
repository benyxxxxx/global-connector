FROM ghcr.io/astral-sh/uv:debian

WORKDIR /app

# Copy dependency files first to leverage Docker cache
COPY pyproject.toml .python-version uv.lock README.md ./

# Install project dependencies
RUN uv sync

# Copy the rest of the project
COPY . .

EXPOSE 8082

CMD ["uv", "run", "service_bot"]