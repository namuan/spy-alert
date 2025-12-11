FROM python:3.12-slim-trixie

# Install uv via pip to avoid slow apt-get update operations
# This is significantly faster and more reliable on slow networks/devices
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files first to leverage Docker layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies
# --frozen: strict lockfile usage
# --no-dev: only production dependencies
# --no-install-project: don't install the project package itself yet (just deps)
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of the application
COPY . .

# Install the project itself
RUN uv sync --frozen --no-dev

# Set the entrypoint command
# We use 'uv run' to ensure the environment is correctly set up
CMD ["uv", "run", "--no-dev", "python", "-m", "spy_sma_alert_bot.main"]
