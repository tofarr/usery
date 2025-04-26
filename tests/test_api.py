import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from usery.main import app
from usery.db.session import get_db
from usery.models.user import Base

# Create a test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create async engine and session
engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)


# Override the get_db dependency
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


# Create test client
client = TestClient(app)

# Override the dependencies
app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="module")
async def setup_database():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create a test user
    from usery.services.security import get_password_hash
    from usery.models.user import User
    
    async with TestingSessionLocal() as session:
        test_user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("password123"),
            full_name="Test User",
            is_active=True,
        )
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
    
    yield
    
    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_login(setup_database):
    # Test login with valid credentials
    response = client.post(
        "/api/v1/auth/login/json",
        json={"username": "testuser", "password": "password123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"
    
    # Test login with invalid credentials
    response = client.post(
        "/api/v1/auth/login/json",
        json={"username": "testuser", "password": "wrongpassword"},
    )
    assert response.status_code == 401