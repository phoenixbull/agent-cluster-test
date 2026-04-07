"""
Pytest 配置和 Fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator

from app.database import Base, get_db
from app.main import app
from app.core.security import get_password_hash

# 创建测试数据库
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def test_db() -> Generator:
    """创建测试数据库表"""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(test_db):
    """每个测试函数使用独立的事务"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    from app.models.user import User
    
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("TestPass123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_token(test_user):
    """创建测试 Token"""
    from app.core.security import create_access_token
    
    return create_access_token(
        data={"sub": str(test_user.id), "email": test_user.email}
    )


@pytest.fixture
def authenticated_client(client, test_token):
    """创建已认证的测试客户端"""
    client.headers = {"Authorization": f"Bearer {test_token}"}
    return client
