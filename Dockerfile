FROM python:3.9-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry==2.1.2

# Copy poetry configuration files
COPY pyproject.toml poetry.lock* /app/

# Configure poetry to not use a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy the rest of the application
COPY . /app/

# Create a non-root user to run the application
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Run migrations and start the application
CMD alembic upgrade head && uvicorn usery.main:app --host 0.0.0.0 --port 8000