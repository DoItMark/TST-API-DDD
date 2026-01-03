"""
Demo script to test the Item Management API
"""
import requests
import json
from time import sleep

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_response(response):
    print(f"\nStatus Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

# Give the server a moment to start
sleep(2)

# 1. Health Check
print_section("1. Health Check")
response = requests.get(f"{BASE_URL}/health")
print_response(response)

# 2. Register a new user
print_section("2. Register New User")
register_data = {
    "username": "demo_user",
    "password": "demo123"
}
response = requests.post(f"{BASE_URL}/register", json=register_data)
print_response(response)

# 3. Login and get token
print_section("3. Login and Get JWT Token")
login_data = {
    "username": "demo_user",
    "password": "demo123"
}
response = requests.post(f"{BASE_URL}/login", json=login_data)
print_response(response)

if response.status_code == 200:
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get seller_id from registration
    register_response = requests.post(f"{BASE_URL}/login", json=login_data)
    
    # Extract seller_id by registering and checking the response
    # For demo, we'll use a new seller_id from another registration
    seller_data = {
        "username": "seller_demo",
        "password": "seller123"
    }
    seller_reg = requests.post(f"{BASE_URL}/register", json=seller_data)
    seller_id = seller_reg.json().get("seller_id") if seller_reg.status_code == 201 else "00000000-0000-0000-0000-000000000000"
    
    # 4. Create a listing
    print_section("4. Create a New Listing")
    listing_data = {
        "seller_id": seller_id,
        "title": "Vintage Camera",
        "price": {
            "amount": 299.99,
            "currency": "USD"
        },
        "condition": {
            "score": 8,
            "detailed_description": "Good condition with minor wear",
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
    response = requests.post(f"{BASE_URL}/listings", json=listing_data, headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        listing_id = response.json()["listing_id"]
        
        # 5. Get the listing
        print_section("5. Get Listing Details")
        response = requests.get(f"{BASE_URL}/listings/{listing_id}", headers=headers)
        print_response(response)
        
        # 6. Update price
        print_section("6. Update Listing Price")
        price_update = {
            "amount": 279.99,
            "currency": "USD"
        }
        response = requests.patch(f"{BASE_URL}/listings/{listing_id}/price", 
                                json=price_update, headers=headers)
        print_response(response)
        
        # 7. Create another listing
        print_section("7. Create Another Listing")
        listing_data2 = {
            "seller_id": seller_id,
            "title": "Vintage Film Camera Lens",
            "price": {
                "amount": 150.00,
                "currency": "USD"
            },
            "condition": {
                "score": 9,
                "detailed_description": "Excellent condition",
                "known_defects": []
            },
            "attributes": [
                {
                    "name": "brand",
                    "value": "Canon"
                },
                {
                    "name": "focal_length",
                    "value": "50mm"
                }
            ]
        }
        response = requests.post(f"{BASE_URL}/listings", json=listing_data2, headers=headers)
        print_response(response)
        
        # 8. List all active listings
        print_section("8. List All Active Listings")
        response = requests.get(f"{BASE_URL}/listings?item_state=Active", headers=headers)
        print_response(response)
        
        # 9. Search listings
        print_section("9. Search for 'Camera'")
        response = requests.get(f"{BASE_URL}/search?query=camera&min_relevance=0.5", 
                              headers=headers)
        print_response(response)
        
        # 10. Delist a listing
        print_section("10. Delist the First Listing")
        delist_data = {
            "code": "SOLD",
            "explanation": "Item was sold to a buyer"
        }
        response = requests.patch(f"{BASE_URL}/listings/{listing_id}/delist", 
                                json=delist_data, headers=headers)
        print_response(response)
        
        # 11. List all listings (including delisted)
        print_section("11. List All Listings (All States)")
        response = requests.get(f"{BASE_URL}/listings", headers=headers)
        print_response(response)

print_section("Demo Complete!")
print("\nYou can also explore the API interactively at:")
print(f"- Swagger UI: {BASE_URL}/docs")
print(f"- ReDoc: {BASE_URL}/redoc")
