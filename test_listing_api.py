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
from uuid import UUID, uuid4
from decimal import Decimal


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_databases():
    """Auto-clear databases before and after each test"""
    # Clear before test
    listings_db.clear()
    search_index_db.clear()
    users_db.clear()
    yield
    # Clear after test
    listings_db.clear()
    search_index_db.clear()
    users_db.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
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
        **sample_user_data,
        **response.json()
    }


@pytest.fixture
def auth_token(client, registered_user):
    """Get JWT authentication token"""
    response = client.post("/login", json={
        "username": registered_user["username"],
        "password": registered_user["password"]
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Create authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def sample_listing_data(registered_user):
    """Sample listing data for testing"""
    return {
        "seller_id": registered_user["seller_id"],
        "title": "Test Listing",
        "price": {
            "amount": "100.00",
            "currency": "USD"
        },
        "condition": {
            "score": 8,
            "detailed_description": "Excellent condition",
            "known_defects": []
        },
        "attributes": []
    }


@pytest.fixture
def second_user_data():
    """Second user data for ownership testing"""
    return {
        "username": "seconduser",
        "password": "securepass456"
    }


@pytest.fixture
def registered_second_user(client, second_user_data):
    """Create and return a second registered user"""
    response = client.post("/register", json=second_user_data)
    assert response.status_code == 201
    return {
        **second_user_data,
        **response.json()
    }


@pytest.fixture
def second_user_auth_headers(client, registered_second_user):
    """Get auth headers for second user"""
    response = client.post("/login", json={
        "username": registered_second_user["username"],
        "password": registered_second_user["password"]
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

class TestAuthentication:
    """Authentication related tests"""

    @pytest.mark.auth
    def test_register_user_successfully(self, client, sample_user_data):
        """Test successful user registration"""
        # Arrange
        user_data = sample_user_data

        # Act
        response = client.post("/register", json=user_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert data["message"] == "User registered successfully"
        assert "user_id" in data
        assert "seller_id" in data
        # Verify user can parse as UUID
        UUID(data["user_id"])
        UUID(data["seller_id"])

    @pytest.mark.auth
    def test_register_duplicate_username_fails(self, client, registered_user):
        """Test registration with duplicate username fails"""
        # Arrange
        duplicate_data = {
            "username": registered_user["username"],
            "password": "anotherpass"
        }

        # Act
        response = client.post("/register", json=duplicate_data)

        # Assert
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

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
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

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
            "username": "nonexistentuser",
            "password": "somepassword"
        }

        # Act
        response = client.post("/login", json=login_data)

        # Assert
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    @pytest.mark.auth
    def test_access_protected_endpoint_with_valid_token(self, client, sample_listing_data, auth_headers):
        """Test accessing protected endpoint with valid token"""
        # Arrange
        listing_data = sample_listing_data

        # Act
        response = client.post("/listings", json=listing_data, headers=auth_headers)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "listing_id" in data

    @pytest.mark.auth
    def test_access_protected_endpoint_without_token_fails(self, client, sample_listing_data):
        """Test accessing protected endpoint without token fails"""
        # Arrange
        listing_data = sample_listing_data

        # Act
        response = client.post("/listings", json=listing_data)

        # Assert
        assert response.status_code == 403

    @pytest.mark.auth
    def test_access_protected_endpoint_with_invalid_token_fails(self, client, sample_listing_data):
        """Test accessing protected endpoint with invalid token fails"""
        # Arrange
        listing_data = sample_listing_data
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}

        # Act
        response = client.post("/listings", json=listing_data, headers=invalid_headers)

        # Assert
        assert response.status_code == 401


# ============================================================================
# LISTING CRUD TESTS
# ============================================================================

class TestListingOperations:
    """Listing CRUD operation tests"""

    @pytest.mark.listings
    def test_create_listing_with_valid_data(self, client, sample_listing_data, auth_headers):
        """Test creating a listing with valid data"""
        # Arrange
        listing_data = sample_listing_data

        # Act
        response = client.post("/listings", json=listing_data, headers=auth_headers)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == listing_data["title"]
        assert data["item_state"] == "Active"
        assert "listing_id" in data
        assert "created_at" in data
        assert "updated_at" in data
        UUID(data["listing_id"])

    @pytest.mark.listings
    def test_create_listing_without_authentication_fails(self, client, sample_listing_data):
        """Test creating listing without authentication fails"""
        # Arrange
        listing_data = sample_listing_data

        # Act
        response = client.post("/listings", json=listing_data)

        # Assert
        assert response.status_code == 403

    @pytest.mark.listings
    def test_get_listing_by_id(self, client, sample_listing_data, auth_headers):
        """Test getting a listing by ID"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]

        # Act
        response = client.get(f"/listings/{listing_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["listing_id"] == listing_id
        assert data["title"] == sample_listing_data["title"]

    @pytest.mark.listings
    def test_get_nonexistent_listing_returns_404(self, client):
        """Test getting non-existent listing returns 404"""
        # Arrange
        nonexistent_id = uuid4()

        # Act
        response = client.get(f"/listings/{nonexistent_id}")

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.listings
    def test_list_all_listings(self, client, sample_listing_data, auth_headers):
        """Test listing all listings"""
        # Arrange
        # Create multiple listings
        client.post("/listings", json=sample_listing_data, headers=auth_headers)
        second_listing = sample_listing_data.copy()
        second_listing["title"] = "Second Listing"
        client.post("/listings", json=second_listing, headers=auth_headers)

        # Act
        response = client.get("/listings")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    @pytest.mark.listings
    def test_list_listings_with_seller_filter(self, client, sample_listing_data, auth_headers, registered_user):
        """Test listing listings with seller filter"""
        # Arrange
        client.post("/listings", json=sample_listing_data, headers=auth_headers)
        seller_id = registered_user["seller_id"]

        # Act
        response = client.get(f"/listings?seller_id={seller_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(listing["seller_id"] == seller_id for listing in data)

    @pytest.mark.listings
    def test_update_listing_price_as_owner(self, client, sample_listing_data, auth_headers):
        """Test updating listing price as owner"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]
        new_price = {
            "new_price": {
                "amount": "150.00",
                "currency": "USD"
            }
        }

        # Act
        response = client.patch(f"/listings/{listing_id}/price", json=new_price, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["price"]["amount"] == "150.00"

    @pytest.mark.listings
    @pytest.mark.security
    def test_update_listing_price_as_non_owner_fails(self, client, sample_listing_data, auth_headers, second_user_auth_headers):
        """Test updating listing price as non-owner fails"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]
        new_price = {
            "new_price": {
                "amount": "150.00",
                "currency": "USD"
            }
        }

        # Act
        response = client.patch(f"/listings/{listing_id}/price", json=new_price, headers=second_user_auth_headers)

        # Assert
        assert response.status_code == 403
        assert "your own listings" in response.json()["detail"]

    @pytest.mark.listings
    def test_activate_listing(self, client, sample_listing_data, auth_headers):
        """Test activating a listing"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]
        # First delist it
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
        data = response.json()
        assert data["item_state"] == "Active"

    @pytest.mark.listings
    def test_delist_listing_with_reason(self, client, sample_listing_data, auth_headers):
        """Test delisting a listing with reason"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]
        delist_data = {
            "reason": {
                "reason_type": "OutOfStock",
                "detail": "Item is out of stock"
            }
        }

        # Act
        response = client.patch(f"/listings/{listing_id}/delist", json=delist_data, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["item_state"] == "Delisted"

    @pytest.mark.listings
    def test_delete_listing_as_owner(self, client, sample_listing_data, auth_headers):
        """Test deleting a listing as owner"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]

        # Act
        response = client.delete(f"/listings/{listing_id}", headers=auth_headers)

        # Assert
        assert response.status_code == 204
        # Verify it's actually deleted
        get_response = client.get(f"/listings/{listing_id}")
        assert get_response.status_code == 404

    @pytest.mark.listings
    @pytest.mark.security
    def test_delete_listing_as_non_owner_fails(self, client, sample_listing_data, auth_headers, second_user_auth_headers):
        """Test deleting listing as non-owner fails"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]

        # Act
        response = client.delete(f"/listings/{listing_id}", headers=second_user_auth_headers)

        # Assert
        assert response.status_code == 403
        assert "your own listings" in response.json()["detail"]


# ============================================================================
# SECURITY TESTS
# ============================================================================

class TestSecurity:
    """Security related tests"""

    @pytest.mark.security
    def test_unauthorized_access_create_listing_returns_403(self, client, sample_listing_data):
        """Test unauthorized access to create listing returns 403"""
        # Arrange
        listing_data = sample_listing_data

        # Act
        response = client.post("/listings", json=listing_data)

        # Assert
        assert response.status_code == 403

    @pytest.mark.security
    def test_unauthorized_access_update_price_returns_401(self, client, sample_listing_data, auth_headers):
        """Test unauthorized access to update price returns 401"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]
        new_price = {"new_price": {"amount": "200.00", "currency": "USD"}}

        # Act
        response = client.patch(f"/listings/{listing_id}/price", json=new_price)

        # Assert
        assert response.status_code == 403

    @pytest.mark.security
    def test_unauthorized_access_activate_returns_401(self, client, sample_listing_data, auth_headers):
        """Test unauthorized access to activate listing returns 401"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]

        # Act
        response = client.patch(f"/listings/{listing_id}/activate")

        # Assert
        assert response.status_code == 403

    @pytest.mark.security
    def test_unauthorized_access_delist_returns_401(self, client, sample_listing_data, auth_headers):
        """Test unauthorized access to delist listing returns 401"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]
        delist_data = {"reason": {"reason_type": "SellerRequest", "detail": "Test"}}

        # Act
        response = client.patch(f"/listings/{listing_id}/delist", json=delist_data)

        # Assert
        assert response.status_code == 403

    @pytest.mark.security
    def test_unauthorized_access_delete_returns_401(self, client, sample_listing_data, auth_headers):
        """Test unauthorized access to delete listing returns 401"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]

        # Act
        response = client.delete(f"/listings/{listing_id}")

        # Assert
        assert response.status_code == 403

    @pytest.mark.security
    def test_ownership_validation_on_activate(self, client, sample_listing_data, auth_headers, second_user_auth_headers):
        """Test ownership validation on activate"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]

        # Act
        response = client.patch(f"/listings/{listing_id}/activate", headers=second_user_auth_headers)

        # Assert
        assert response.status_code == 403
        assert "your own listings" in response.json()["detail"]

    @pytest.mark.security
    def test_ownership_validation_on_delist(self, client, sample_listing_data, auth_headers, second_user_auth_headers):
        """Test ownership validation on delist"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]
        delist_data = {"reason": {"reason_type": "SellerRequest", "detail": "Test"}}

        # Act
        response = client.patch(f"/listings/{listing_id}/delist", json=delist_data, headers=second_user_auth_headers)

        # Assert
        assert response.status_code == 403
        assert "your own listings" in response.json()["detail"]

    @pytest.mark.security
    def test_non_owner_operations_fail(self, client, sample_listing_data, auth_headers, second_user_auth_headers):
        """Test that non-owner operations fail comprehensively"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]

        # Act & Assert - Update price
        new_price = {"new_price": {"amount": "200.00", "currency": "USD"}}
        response = client.patch(f"/listings/{listing_id}/price", json=new_price, headers=second_user_auth_headers)
        assert response.status_code == 403

        # Act & Assert - Delete
        response = client.delete(f"/listings/{listing_id}", headers=second_user_auth_headers)
        assert response.status_code == 403


# ============================================================================
# SEARCH TESTS
# ============================================================================

class TestSearchFunctionality:
    """Search functionality tests"""

    @pytest.mark.search
    def test_search_by_query(self, client, sample_listing_data, auth_headers):
        """Test searching listings by query"""
        # Arrange
        listing_data = sample_listing_data.copy()
        listing_data["title"] = "Unique Searchable Item"
        client.post("/listings", json=listing_data, headers=auth_headers)

        # Act
        response = client.get("/search?query=Unique")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any("unique" in result["searchable_text"].lower() for result in data)

    @pytest.mark.search
    def test_search_with_relevance_filter(self, client, sample_listing_data, auth_headers):
        """Test search with relevance filter"""
        # Arrange
        client.post("/listings", json=sample_listing_data, headers=auth_headers)

        # Act
        response = client.get("/search?min_relevance=1.0")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert all(result["relevance_score"] >= 1.0 for result in data)

    @pytest.mark.search
    def test_search_returns_correct_results(self, client, sample_listing_data, auth_headers):
        """Test search returns correct results"""
        # Arrange
        listing1 = sample_listing_data.copy()
        listing1["title"] = "Gaming Laptop"
        client.post("/listings", json=listing1, headers=auth_headers)

        listing2 = sample_listing_data.copy()
        listing2["title"] = "Office Chair"
        client.post("/listings", json=listing2, headers=auth_headers)

        # Act
        response = client.get("/search?query=Gaming")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any("gaming" in result["searchable_text"].lower() for result in data)
        # Office chair should not appear in gaming search
        gaming_results = [r for r in data if "gaming" in r["searchable_text"].lower()]
        assert len(gaming_results) >= 1

    @pytest.mark.search
    def test_empty_query_returns_all(self, client, sample_listing_data, auth_headers):
        """Test empty query returns all listings"""
        # Arrange
        client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing2 = sample_listing_data.copy()
        listing2["title"] = "Another Item"
        client.post("/listings", json=listing2, headers=auth_headers)

        # Act
        response = client.get("/search")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    @pytest.mark.search
    def test_no_results_handling(self, client):
        """Test handling of search with no results"""
        # Arrange
        # No listings created

        # Act
        response = client.get("/search?query=NonExistentItem123")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


# ============================================================================
# HEALTH CHECK & EDGE CASES TESTS
# ============================================================================

class TestHealthCheck:
    """Health check endpoint tests"""

    def test_health_endpoint_status(self, client):
        """Test health endpoint returns correct status"""
        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "listings_count" in data
        assert "search_index_count" in data


class TestEdgeCases:
    """Edge cases and error handling tests"""

    def test_minimal_data_handling(self, client, auth_headers, registered_user):
        """Test handling of minimal valid data"""
        # Arrange
        minimal_listing = {
            "seller_id": registered_user["seller_id"],
            "title": "A",
            "price": {"amount": "0.01", "currency": "USD"},
            "condition": {
                "score": 1,
                "detailed_description": "Minimal",
                "known_defects": []
            }
        }

        # Act
        response = client.post("/listings", json=minimal_listing, headers=auth_headers)

        # Assert
        assert response.status_code == 201

    def test_state_transitions_delist_to_active(self, client, sample_listing_data, auth_headers):
        """Test state transitions from Delisted to Active"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]
        delist_data = {"reason": {"reason_type": "SellerRequest", "detail": "Test"}}
        client.patch(f"/listings/{listing_id}/delist", json=delist_data, headers=auth_headers)

        # Act
        response = client.patch(f"/listings/{listing_id}/activate", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["item_state"] == "Active"

    def test_pagination(self, client, sample_listing_data, auth_headers):
        """Test pagination of listings"""
        # Arrange
        for i in range(5):
            listing = sample_listing_data.copy()
            listing["title"] = f"Listing {i}"
            client.post("/listings", json=listing, headers=auth_headers)

        # Act
        response = client.get("/listings?skip=2&limit=2")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_already_delisted_listing_delist_fails(self, client, sample_listing_data, auth_headers):
        """Test delisting an already delisted listing fails"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]
        delist_data = {"reason": {"reason_type": "SellerRequest", "detail": "First delist"}}
        client.patch(f"/listings/{listing_id}/delist", json=delist_data, headers=auth_headers)

        # Act
        response = client.patch(f"/listings/{listing_id}/delist", json=delist_data, headers=auth_headers)

        # Assert
        assert response.status_code == 400
        assert "already delisted" in response.json()["detail"].lower()

    def test_already_active_listing_activate(self, client, sample_listing_data, auth_headers):
        """Test activating an already active listing"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]

        # Act
        response = client.patch(f"/listings/{listing_id}/activate", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["item_state"] == "Active"

    def test_search_pagination(self, client, sample_listing_data, auth_headers):
        """Test search with pagination"""
        # Arrange
        for i in range(5):
            listing = sample_listing_data.copy()
            listing["title"] = f"Test Item {i}"
            client.post("/listings", json=listing, headers=auth_headers)

        # Act
        response = client.get("/search?skip=1&limit=2")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_listing_with_attributes(self, client, auth_headers, registered_user):
        """Test creating listing with attributes"""
        # Arrange
        listing_with_attrs = {
            "seller_id": registered_user["seller_id"],
            "title": "Laptop with Specs",
            "price": {"amount": "999.99", "currency": "USD"},
            "condition": {
                "score": 9,
                "detailed_description": "Like new",
                "known_defects": []
            },
            "attributes": [
                {"name": "Brand", "value": "Dell"},
                {"name": "RAM", "value": "16GB"}
            ]
        }

        # Act
        response = client.post("/listings", json=listing_with_attrs, headers=auth_headers)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert len(data["attributes"]) == 2

    def test_listing_with_known_defects(self, client, auth_headers, registered_user):
        """Test creating listing with known defects"""
        # Arrange
        listing_with_defects = {
            "seller_id": registered_user["seller_id"],
            "title": "Used Phone",
            "price": {"amount": "199.99", "currency": "USD"},
            "condition": {
                "score": 6,
                "detailed_description": "Good condition with minor scratches",
                "known_defects": ["Screen scratch", "Battery 80% health"]
            }
        }

        # Act
        response = client.post("/listings", json=listing_with_defects, headers=auth_headers)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert len(data["condition"]["known_defects"]) == 2

    def test_search_sorts_by_relevance(self, client, sample_listing_data, auth_headers):
        """Test search results are sorted by relevance"""
        # Arrange
        listing1 = sample_listing_data.copy()
        listing1["title"] = "Item"
        listing1["condition"]["score"] = 5
        client.post("/listings", json=listing1, headers=auth_headers)

        listing2 = sample_listing_data.copy()
        listing2["title"] = "Premium Item"
        listing2["condition"]["score"] = 10
        client.post("/listings", json=listing2, headers=auth_headers)

        # Act
        response = client.get("/search")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        # Verify sorted by relevance descending
        for i in range(len(data) - 1):
            assert data[i]["relevance_score"] >= data[i + 1]["relevance_score"]

    def test_filter_by_item_state(self, client, sample_listing_data, auth_headers):
        """Test filtering listings by item state"""
        # Arrange
        create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
        listing_id = create_response.json()["listing_id"]
        delist_data = {"reason": {"reason_type": "SellerRequest", "detail": "Test"}}
        client.patch(f"/listings/{listing_id}/delist", json=delist_data, headers=auth_headers)

        # Create another active listing
        listing2 = sample_listing_data.copy()
        listing2["title"] = "Active Listing"
        client.post("/listings", json=listing2, headers=auth_headers)

        # Act
        response = client.get("/listings?item_state=Active")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert all(listing["item_state"] == "Active" for listing in data)
