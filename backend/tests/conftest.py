"""
Pytest fixtures for testing the Public Incentives API

This module provides fixtures for:
- Database connections
- Test client
- Sample data
- Mocked services
"""

import pytest
import sys
from pathlib import Path
from typing import Generator

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock, patch
import os

from app.main import app
from app.db.database import Base
from app.db.models import Incentive, IncentiveMetadata, Company, IncentiveCompanyMatch


def get_db():
    """Dummy get_db for tests"""
    pass


# Test database URL (use in-memory SQLite for COMPLETE ISOLATION)
# Using ':memory:' means database only exists in RAM during tests
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    """Create test database engine with in-memory SQLite"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    # No cleanup needed - in-memory database disappears automatically


@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    """Create a database session for testing with complete isolation"""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    yield session
    
    # Cleanup: rollback transaction to remove all test data
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    """Create test client with database session override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_incentive_data():
    """Sample incentive data for testing"""
    import uuid
    return {
        "incentive_id": uuid.UUID("123e4567-e89b-12d3-a456-426614174000"),
        "title": "Incentivo Teste",
        "description": "Descrição do incentivo de teste",
        "ai_description": {"type": "investment", "areas": ["technology"]},
        "document_urls": ["https://example.com/doc1.pdf"],
        "total_budget": 1000000.0,
        "source_link": "https://example.com/incentive"
    }


@pytest.fixture
def sample_company_data():
    """Sample company data for testing"""
    import uuid
    return {
        "company_id": uuid.UUID("456e7890-e89b-12d3-a456-426614174001"),
        "company_name": "Teste Software Lda",
        "cae_primary_label": "Software development",
        "trade_description_native": "Desenvolvimento de software customizado",
        "website": "https://testesoftware.pt",
        "cae_primary_code": ["62010"],
        "company_size": "medium",
        "region": "Lisboa",
        "is_active": True
    }


@pytest.fixture
def create_incentive(db_session: Session, sample_incentive_data):
    """Create a test incentive in the database"""
    import uuid
    incentive = Incentive(**sample_incentive_data)
    db_session.add(incentive)
    db_session.commit()
    db_session.refresh(incentive)
    
    # Create metadata
    metadata = IncentiveMetadata(
        metadata_id=uuid.uuid4(),
        incentive_id=incentive.incentive_id,
        raw_csv_data={"test": "data"},
        ai_processing_status="completed"
    )
    db_session.add(metadata)
    db_session.commit()
    
    return incentive


@pytest.fixture
def create_company(db_session: Session, sample_company_data):
    """Create a test company in the database"""
    company = Company(**sample_company_data)
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    return {
        "choices": [
            {
                "message": {
                    "content": '{"type": "investment", "areas": ["technology"], "description": "Test description"}'
                }
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
    }


@pytest.fixture
def mock_ai_processor(mock_openai_response):
    """Mock AI processor to avoid calling real OpenAI API"""
    with patch('app.services.ai_processor.AIProcessor') as mock:
        instance = Mock()
        instance.process_incentive_complete.return_value = True
        instance.analyze_company_matches.return_value = [
            {"company_name": "Test Company", "match_score": 0.85}
        ]
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service to avoid calling real OpenAI API"""
    with patch('app.services.embedding_service.EmbeddingService') as mock:
        instance = Mock()
        instance.get_embedding.return_value = [0.1] * 1536  # Standard embedding size
        mock.return_value = instance
        yield instance


# Markers for test organization
pytest.mark.api = pytest.mark.mark("api")
pytest.mark.unit = pytest.mark.mark("unit")
pytest.mark.integration = pytest.mark.mark("integration")
pytest.mark.slow = pytest.mark.mark("slow")

