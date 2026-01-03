"""
Comprehensive Test Suite for Item Management API
Following TDD (Test-Driven Development) principles with AAA pattern
"""

import pytest
from fastapi.testclient import TestClient
from listing_api import (
    app, listings_db, search_index_db, users_db,
    Money, Condition, DelistReason, ReasonType, ItemState
)
from uuid import uuid4, UUID
from decimal import Decimal


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_databases():
    """Clear all in-memory databases before each test"""
    listings_db.clear()
    search_index_db.clear()
    users_db.clear()
    yield
    listings_db.clear()
    search_index_db.clear()
    users_db.clear()


@pytest.fixture
def sample_user_data():
    """Sample user registration data"""
    return {
        "username": "testuser",
        "password": "testpass123"
    }


@pytest.fixture
def registered_user(client, sample_user_data):
    """Create and return a registered user"""
    response = client.post("/register", json=sample_user_data)
    assert response.status_code == 201
    return {
        "username": sample_user_data["username"],
        "password": sample_user_data["password"],
        "user_data": response.json()
    }


@pytest.fixture
def auth_token(client, registered_user):
    """Get authentication token for registered user"""
    login_data = {
        "username": registered_user["username"],
        "password": registered_user["password"]
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Create authorization headers with token"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def sample_listing_data(registered_user):
    """Sample listing creation data"""
    return {
        "seller_id": registered_user["user_data"]["seller_id"],
        "title": "Vintage Camera",
        "price": {
            "amount": "299.99",
            "currency": "USD"
        },
        "condition": {
            "score": 8,
            "detailed_description": "Excellent condition, minor wear",
            "known_defects": ["Small scratch on lens cap"]
        },
        "attributes": [
            {
                "name": "brand",
                "value": "Canon"
            },
            {
                "name": "model",
                "value": "AE-1"
            }
        ]
    }


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

class TestAuthentication:
    """Test suite for authentication endpoints"""

    @pytest.mark.auth
    def test_register_user_success(self, client, sample_user_data):
        """Test successful user registration"""
        # Arrange
        user_data = sample_user_data
        
        # Act
        response = client.post("/register", json=user_data)
        
        # Assert
        assert response.status_code == 201
        json_data = response.json()
        assert json_data["message"] == "User registered successfully"
        assert "user_id" in json_data
        assert "seller_id" in json_data

    @pytest.mark.auth
    def test_register_user_duplicate_username_fails(self, client, sample_user_data):
        """Test registration with duplicate username fails"""
        # Arrange
        client.post("/register", json=sample_user_data)
        
        # Act
        response = client.post("/register", json=sample_user_data)
        
        # Assert
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]

    @pytest.mark.auth
    def test_login_with_correct_credentials(self, client, registered_user):
        """Test login with correct credentials"""
        # Arrange
        login_data = {
            "username": registered_user["username"],
            "password": registered_user["password"]
        }
        
        # Act
        response = client.post("/login", json=login_data)
        
        # Assert
        assert response.status_code == 200
        json_data = response.json()
        assert "access_token" in json_data
        assert json_data["token_type"] == "bearer"

    @pytest.mark.auth
    def test_login_with_wrong_password_fails(self, client, registered_user):
        """Test login with wrong password fails"""
        # Arrange
        login_data = {
            "username": registered_user["username"],
            "password": "wrongpassword"
        }
        
        # Act
        response = client.post("/login", json=login_data)
        
        # Assert
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    @pytest.mark.auth
    def test_login_with_nonexistent_user_fails(self, client):
        """Test login with non-existent user fails"""
        # Arrange
        login_data = {
            "username": "nonexistent",
            "password": "anypassword"
        }
        
        # Act
        response = client.post("/login", json=login_data)
        
        # Assert
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    @pytest.mark.auth
    @pytest.mark.security
    def test_access_protected_endpoint_with_valid_token(self, client, auth_headers, sample_listing_data):
        """Test access to protected endpoint with valid token"""
        # Arrange & Act
        response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        
        # Assert
        assert response.status_code == 201

    @pytest.mark.auth
    @pytest.mark.security
    def test_access_protected_endpoint_without_token_fails(self, client, sample_listing_data):
        """Test access to protected endpoint without token fails"""
        # Act
        response = client.post("/listings", json=sample_listing_data)
        
        # Assert
        assert response.status_code == 403

    @pytest.mark.auth
    @pytest.mark.security
    def test_access_protected_endpoint_with_invalid_token_fails(self, client, sample_listing_data):
        """Test access to protected endpoint with invalid token fails"""
        # Arrange
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}
        
        # Act
        response = client.post("/listings", json=sample_listing_data, headers=invalid_headers)
        
        # Assert
        assert response.status_code == 401


# ============================================================================
# LISTING CRUD TESTS
# ============================================================================

class TestListingOperations:
    """Test suite for listing CRUD operations"""

    @pytest.mark.listings
    def test_create_listing_with_valid_data(self, client, auth_headers, sample_listing_data):
        """Test creating a listing with valid data"""
        # Act
        response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        
        # Assert
        assert response.status_code == 201
        json_data = response.json()
        assert json_data["title"] == sample_listing_data["title"]
        assert json_data["item_state"] == "Active"
        assert "listing_id" in json_data
        assert Decimal(json_data["price"]["amount"]) == Decimal(sample_listing_data["price"]["amount"])

    @pytest.mark.listings
    @pytest.mark.security
    def test_create_listing_without_authentication_fails(self, client, sample_listing_data):
        """Test creating a listing without authentication fails"""
        # Act
        response = client.post("/listings", json=sample_listing_data)
        
        # Assert
        assert response.status_code == 403

    @pytest.mark.listings
    def test_get_listing_by_id(self, client, auth_headers, sample_listing_data):
        """Test retrieving a listing by ID"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]
        
        # Act
        response = client.get(f"/listings/{listing_id}")
        
        # Assert
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["listing_id"] == listing_id
        assert json_data["title"] == sample_listing_data["title"]

    @pytest.mark.listings
    def test_get_nonexistent_listing_returns_404(self, client):
        """Test getting non-existent listing returns 404"""
        # Arrange
        nonexistent_id = str(uuid4())
        
        # Act
        response = client.get(f"/listings/{nonexistent_id}")
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.listings
    def test_list_all_listings(self, client, auth_headers, sample_listing_data):
        """Test listing all listings"""
        # Arrange
        client.post("/listings", json=sample_listing_data, headers=auth_headers)
        
        # Act
        response = client.get("/listings")
        
        # Assert
        assert response.status_code == 200
        json_data = response.json()
        assert isinstance(json_data, list)
        assert len(json_data) >= 1

    @pytest.mark.listings
    def test_list_listings_with_seller_filter(self, client, auth_headers, sample_listing_data, registered_user):
        """Test listing listings filtered by seller"""
        # Arrange
        client.post("/listings", json=sample_listing_data, headers=auth_headers)
        seller_id = registered_user["user_data"]["seller_id"]
        
        # Act
        response = client.get(f"/listings?seller_id={seller_id}")
        
        # Assert
        assert response.status_code == 200
        json_data = response.json()
        assert len(json_data) >= 1
        for listing in json_data:
            assert listing["seller_id"] == seller_id

    @pytest.mark.listings
    def test_update_listing_price_owner(self, client, auth_headers, sample_listing_data):
        """Test updating listing price by owner"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]
        new_price_data = {
            "new_price": {
                "amount": "349.99",
                "currency": "USD"
            }
        }
        
        # Act
        response = client.patch(f"/listings/{listing_id}/price", json=new_price_data, headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        json_data = response.json()
        assert Decimal(json_data["price"]["amount"]) == Decimal("349.99")

    @pytest.mark.listings
    @pytest.mark.security
    def test_update_listing_price_non_owner_fails(self, client, sample_listing_data):
        """Test updating listing price by non-owner fails"""
        # Arrange - Create first user and listing
        user1_data = {"username": "user1", "password": "pass123"}
        client.post("/register", json=user1_data)
        login1_response = client.post("/login", json=user1_data)
        token1 = login1_response.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        create_response = client.post("/listings", json=sample_listing_data, headers=headers1)
        listing_id = create_response.json()["listing_id"]
        
        # Create second user
        user2_data = {"username": "user2", "password": "pass123"}
        client.post("/register", json=user2_data)
        login2_response = client.post("/login", json=user2_data)
        token2 = login2_response.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        new_price_data = {
            "new_price": {
                "amount": "999.99",
                "currency": "USD"
            }
        }
        
        # Act - Try to update with second user
        response = client.patch(f"/listings/{listing_id}/price", json=new_price_data, headers=headers2)
        
        # Assert
        assert response.status_code == 403
        assert "only update price of your own listings" in response.json()["detail"]

    @pytest.mark.listings
    def test_activate_listing(self, client, auth_headers, sample_listing_data):
        """Test activating a listing"""
        # Arrange - Create and delist a listing first
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]
        
        delist_data = {
            "reason": {
                "reason_type": "SellerRequest",
                "detail": "Temporarily unavailable"
            }
        }
        client.patch(f"/listings/{listing_id}/delist", json=delist_data, headers=auth_headers)
        
        # Act
        response = client.patch(f"/listings/{listing_id}/activate", headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["item_state"] == "Active"

    @pytest.mark.listings
    def test_delist_listing_with_reason(self, client, auth_headers, sample_listing_data):
        """Test delisting a listing with a reason"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]
        
        delist_data = {
            "reason": {
                "reason_type": "OutOfStock",
                "detail": "Item sold elsewhere"
            }
        }
        
        # Act
        response = client.patch(f"/listings/{listing_id}/delist", json=delist_data, headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["item_state"] == "Delisted"

    @pytest.mark.listings
    def test_delete_listing_owner(self, client, auth_headers, sample_listing_data):
        """Test deleting a listing by owner"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]
        
        # Act
        response = client.delete(f"/listings/{listing_id}", headers=auth_headers)
        
        # Assert
        assert response.status_code == 204
        
        # Verify listing is deleted
        get_response = client.get(f"/listings/{listing_id}")
        assert get_response.status_code == 404

    @pytest.mark.listings
    @pytest.mark.security
    def test_delete_listing_non_owner_fails(self, client, sample_listing_data):
        """Test deleting a listing by non-owner fails"""
        # Arrange - Create first user and listing
        user1_data = {"username": "user1", "password": "pass123"}
        client.post("/register", json=user1_data)
        login1_response = client.post("/login", json=user1_data)
        token1 = login1_response.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        create_response = client.post("/listings", json=sample_listing_data, headers=headers1)
        listing_id = create_response.json()["listing_id"]
        
        # Create second user
        user2_data = {"username": "user2", "password": "pass123"}
        client.post("/register", json=user2_data)
        login2_response = client.post("/login", json=user2_data)
        token2 = login2_response.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Act - Try to delete with second user
        response = client.delete(f"/listings/{listing_id}", headers=headers2)
        
        # Assert
        assert response.status_code == 403
        assert "only delete your own listings" in response.json()["detail"]


# ============================================================================
# SEARCH TESTS
# ============================================================================

class TestSearchFunctionality:
    """Test suite for search functionality"""

    @pytest.mark.search
    def test_search_listings_by_query(self, client, auth_headers, sample_listing_data):
        """Test searching listings by query"""
        # Arrange
        client.post("/listings", json=sample_listing_data, headers=auth_headers)
        
        # Act
        response = client.get("/search?query=camera")
        
        # Assert
        assert response.status_code == 200
        json_data = response.json()
        assert isinstance(json_data, list)
        assert len(json_data) >= 1

    @pytest.mark.search
    def test_search_with_relevance_filter(self, client, auth_headers, sample_listing_data):
        """Test searching with relevance filter"""
        # Arrange
        client.post("/listings", json=sample_listing_data, headers=auth_headers)
        
        # Act
        response = client.get("/search?min_relevance=1.0")
        
        # Assert
        assert response.status_code == 200
        json_data = response.json()
        assert isinstance(json_data, list)
        for item in json_data:
            assert item["relevance_score"] >= 1.0

    @pytest.mark.search
    def test_search_returns_correct_results(self, client, auth_headers):
        """Test search returns correct and sorted results"""
        # Arrange - Create multiple listings
        listing1 = {
            "seller_id": str(uuid4()),
            "title": "Vintage Camera",
            "price": {"amount": "299.99", "currency": "USD"},
            "condition": {
                "score": 8,
                "detailed_description": "Good condition",
                "known_defects": []
            },
            "attributes": []
        }
        listing2 = {
            "seller_id": str(uuid4()),
            "title": "Modern Laptop",
            "price": {"amount": "999.99", "currency": "USD"},
            "condition": {
                "score": 9,
                "detailed_description": "Excellent condition",
                "known_defects": []
            },
            "attributes": []
        }
        
        client.post("/listings", json=listing1, headers=auth_headers)
        client.post("/listings", json=listing2, headers=auth_headers)
        
        # Act
        response = client.get("/search?query=camera")
        
        # Assert
        assert response.status_code == 200
        json_data = response.json()
        assert len(json_data) >= 1
        # Check that camera listing is in results
        camera_found = any("camera" in item["searchable_text"].lower() for item in json_data)
        assert camera_found


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

class TestHealthCheck:
    """Test suite for health check endpoint"""

    def test_health_endpoint_returns_correct_status(self, client):
        """Test health endpoint returns correct status"""
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["status"] == "healthy"
        assert "listings_count" in json_data
        assert "search_index_count" in json_data

    def test_health_endpoint_counts_are_accurate(self, client, auth_headers, sample_listing_data):
        """Test health endpoint counts are accurate"""
        # Arrange
        client.post("/listings", json=sample_listing_data, headers=auth_headers)
        
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["listings_count"] == 1
        assert json_data["search_index_count"] == 1


# ============================================================================
# EDGE CASES AND ERROR HANDLING TESTS
# ============================================================================

class TestEdgeCases:
    """Test suite for edge cases and error handling"""

    @pytest.mark.listings
    def test_create_listing_with_minimal_data(self, client, auth_headers):
        """Test creating a listing with minimal required data"""
        # Arrange
        minimal_listing = {
            "seller_id": str(uuid4()),
            "title": "Item",
            "price": {"amount": "10.00", "currency": "USD"},
            "condition": {
                "score": 5,
                "detailed_description": "Average",
                "known_defects": []
            }
        }
        
        # Act
        response = client.post("/listings", json=minimal_listing, headers=auth_headers)
        
        # Assert
        assert response.status_code == 201
        json_data = response.json()
        assert json_data["attributes"] == []

    @pytest.mark.listings
    def test_update_price_of_delisted_listing_succeeds(self, client, auth_headers, sample_listing_data):
        """Test updating price of delisted listing succeeds"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]
        
        # Delist the listing
        delist_data = {
            "reason": {
                "reason_type": "SellerRequest",
                "detail": "Temporarily unavailable"
            }
        }
        client.patch(f"/listings/{listing_id}/delist", json=delist_data, headers=auth_headers)
        
        # Act
        new_price_data = {
            "new_price": {"amount": "399.99", "currency": "USD"}
        }
        response = client.patch(f"/listings/{listing_id}/price", json=new_price_data, headers=auth_headers)
        
        # Assert
        assert response.status_code == 200

    @pytest.mark.search
    def test_search_with_empty_query_returns_all(self, client, auth_headers, sample_listing_data):
        """Test search with empty query returns all listings"""
        # Arrange
        client.post("/listings", json=sample_listing_data, headers=auth_headers)
        
        # Act
        response = client.get("/search")
        
        # Assert
        assert response.status_code == 200
        json_data = response.json()
        assert len(json_data) >= 1

    @pytest.mark.search
    def test_search_with_no_results(self, client):
        """Test search with query that has no results"""
        # Act
        response = client.get("/search?query=nonexistentitem123456")
        
        # Assert
        assert response.status_code == 200
        json_data = response.json()
        assert isinstance(json_data, list)

    @pytest.mark.listings
    def test_activate_already_active_listing_succeeds(self, client, auth_headers, sample_listing_data):
        """Test activating an already active listing succeeds"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]
        
        # Act
        response = client.patch(f"/listings/{listing_id}/activate", headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["item_state"] == "Active"

    @pytest.mark.listings
    def test_delist_already_delisted_listing_fails(self, client, auth_headers, sample_listing_data):
        """Test delisting an already delisted listing fails"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]
        
        delist_data = {
            "reason": {
                "reason_type": "SellerRequest",
                "detail": "Test reason"
            }
        }
        client.patch(f"/listings/{listing_id}/delist", json=delist_data, headers=auth_headers)
        
        # Act - Try to delist again
        response = client.patch(f"/listings/{listing_id}/delist", json=delist_data, headers=auth_headers)
        
        # Assert
        assert response.status_code == 400
        assert "already delisted" in response.json()["detail"]

    @pytest.mark.listings
    def test_listing_pagination(self, client, auth_headers, sample_listing_data):
        """Test listing pagination parameters"""
        # Arrange - Create multiple listings
        for i in range(5):
            listing_data = sample_listing_data.copy()
            listing_data["title"] = f"Item {i}"
            client.post("/listings", json=listing_data, headers=auth_headers)
        
        # Act
        response = client.get("/listings?skip=2&limit=2")
        
        # Assert
        assert response.status_code == 200
        json_data = response.json()
        assert len(json_data) == 2

    @pytest.mark.security
    def test_activate_listing_non_owner_fails(self, client, sample_listing_data):
        """Test activating listing by non-owner fails"""
        # Arrange
        user1_data = {"username": "owner", "password": "pass123"}
        client.post("/register", json=user1_data)
        login1 = client.post("/login", json=user1_data)
        headers1 = {"Authorization": f"Bearer {login1.json()['access_token']}"}
        
        create_response = client.post("/listings", json=sample_listing_data, headers=headers1)
        listing_id = create_response.json()["listing_id"]
        
        user2_data = {"username": "other", "password": "pass123"}
        client.post("/register", json=user2_data)
        login2 = client.post("/login", json=user2_data)
        headers2 = {"Authorization": f"Bearer {login2.json()['access_token']}"}
        
        # Act
        response = client.patch(f"/listings/{listing_id}/activate", headers=headers2)
        
        # Assert
        assert response.status_code == 403

    @pytest.mark.security
    def test_delist_listing_non_owner_fails(self, client, sample_listing_data):
        """Test delisting by non-owner fails"""
        # Arrange
        user1_data = {"username": "owner", "password": "pass123"}
        client.post("/register", json=user1_data)
        login1 = client.post("/login", json=user1_data)
        headers1 = {"Authorization": f"Bearer {login1.json()['access_token']}"}
        
        create_response = client.post("/listings", json=sample_listing_data, headers=headers1)
        listing_id = create_response.json()["listing_id"]
        
        user2_data = {"username": "other", "password": "pass123"}
        client.post("/register", json=user2_data)
        login2 = client.post("/login", json=user2_data)
        headers2 = {"Authorization": f"Bearer {login2.json()['access_token']}"}
        
        delist_data = {
            "reason": {
                "reason_type": "SellerRequest",
                "detail": "Test"
            }
        }
        
        # Act
        response = client.patch(f"/listings/{listing_id}/delist", json=delist_data, headers=headers2)
        
        # Assert
        assert response.status_code == 403
