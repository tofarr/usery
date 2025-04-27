# Usery

A user management system with REST API built with FastAPI, SQLAlchemy, Alembic, and Redis.

## Features

- User management (CRUD operations)
- Authentication with JWT tokens
- Token blacklisting with Redis
- Database migrations with Alembic
- Docker support

## Requirements

- Python 3.9+
- Poetry
- Redis (optional for development)

## Installation

### Using Poetry

```bash
# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### Using Docker

```bash
# Build and start the containers
docker-compose up -d
```

## Database Migrations

```bash
# Generate a new migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

## Running the Application

### Development

```bash
# Run the application with hot reload
uvicorn usery.main:app --reload
```

### Production

```bash
# Run the application
uvicorn usery.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once the application is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

The application can be configured using environment variables or a `.env` file:

- `DATABASE_URL`: Database connection string
- `REDIS_HOST`: Redis host
- `REDIS_PORT`: Redis port
- `REDIS_PASSWORD`: Redis password (optional)
- `SECRET_KEY`: Secret key for general application use
- `JWT_SECRET_KEY`: Secret key for JWT token generation (HS256). If not provided, the system will:
  1. Look for an existing key in the `.jwt_secret` file
  2. If no file exists, generate a random key and save it to `.jwt_secret`
  
  This ensures that tokens remain valid across application restarts.
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time in minutes
- `SUPERUSER_ONLY_CREATE_USERS`: If set to `True`, only superusers can create new users. If `False` (default), anyone can register. Note: The first user created in the system will always be a superuser, regardless of this setting.
- `USER_VISIBILITY`: Controls who can view user information:
  - `private`: Only superusers can list users. Users can view themselves.
  - `protected`: Only active users can list users. Users can view themselves.
  - `public`: No login required to list users.

## Attribute and Tag Permissions

Attributes and tags can be configured with specific permission requirements:

- `edit_requires_superuser`: When set to `True`, only superusers can create, update, or delete user attributes/tags with this attribute/tag. Regular users cannot modify their own attributes/tags if this is set.
- `view_requires_superuser`: When set to `True`, only superusers can view user attributes/tags with this attribute/tag. Regular users cannot view their own attributes/tags if this is set.

This allows for storing sensitive information that should only be accessible to administrators.