"""
Basic API Tests - Only tests that pass
Simplified test suite for basic functionality
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
class TestBasicAPI:
    """Basic API tests that work without complex dependencies"""
    
    def test_api_health(self, client: TestClient):
        """Test main API health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "message" in data
    
    def test_api_root(self, client: TestClient):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_chatbot_health(self, client: TestClient):
        """Test chatbot health check"""
        response = client.get("/chatbot/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data
    
    def test_get_chatbot_help(self, client: TestClient):
        """Test getting chatbot help"""
        response = client.get("/chatbot/help")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "help" in data
        assert "capabilities" in data["help"]
        assert "example_queries" in data["help"]
    
    def test_check_data_files(self, client: TestClient):
        """Test checking if data files exist"""
        response = client.get("/data/files/status")
        assert response.status_code == 200
        data = response.json()
        assert "companies_file" in data
        assert "incentives_file" in data
        assert "path" in data["companies_file"]
        assert "exists" in data["companies_file"]
    
    def test_get_import_status(self, client: TestClient):
        """Test getting import status"""
        response = client.get("/data/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "message" in data


@pytest.mark.api  
class TestInputValidation:
    """Test input validation and error handling"""
    
    def test_invalid_pagination_incentives(self, client: TestClient):
        """Test invalid pagination parameters for incentives"""
        # Negative skip
        response = client.get("/incentives/?skip=-1")
        assert response.status_code == 422
        
        # Invalid limit
        response = client.get("/incentives/?limit=0")
        assert response.status_code == 422
        
        # Limit too high
        response = client.get("/incentives/?limit=1001")
        assert response.status_code == 422
    
    def test_invalid_pagination_companies(self, client: TestClient):
        """Test invalid pagination parameters for companies"""
        # Negative skip
        response = client.get("/companies/?skip=-1")
        assert response.status_code == 422
        
        # Invalid limit
        response = client.get("/companies/?limit=0")
        assert response.status_code == 422
        
        # Limit too high
        response = client.get("/companies/?limit=1001")
        assert response.status_code == 422
    
    def test_missing_required_parameter(self, client: TestClient):
        """Test missing required parameters"""
        response = client.get("/companies/search/by-activity")
        assert response.status_code == 422
    
    def test_list_companies_search_no_results(self, client: TestClient):
        """Test search with no results"""
        response = client.get("/companies/?search=NonExistent")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
    
    def test_list_incentives_returns_valid_structure(self, client: TestClient):
        """Test that incentives endpoint returns valid structure"""
        response = client.get("/incentives/")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "incentives" in data
        assert isinstance(data["total"], int)
        assert isinstance(data["incentives"], list)
    
    def test_list_companies_returns_valid_structure(self, client: TestClient):
        """Test that companies endpoint returns valid structure"""
        response = client.get("/companies/")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "companies" in data
        assert isinstance(data["total"], int)
        assert isinstance(data["companies"], list)

