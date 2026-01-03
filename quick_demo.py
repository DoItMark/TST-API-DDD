"""
Quick Demo Script - Tests the API directly without starting a separate server
"""
import subprocess
import time
import requests
import json
import sys

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_api():
    BASE_URL = "http://localhost:8000"
    
    # Test health endpoint
    print_section("1. Testing Health Check Endpoint")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    # Register user
    print_section("2. Registering New User")
    try:
        response = requests.post(
            f"{BASE_URL}/register",
            json={"username": f"demo_{int(time.time())}", "password": "pass123"},
            timeout=5
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            user_id = response.json()["user_id"]
            username = response.json()["username"]
            
            # Login
            print_section("3. Logging In")
            response = requests.post(
                f"{BASE_URL}/login",
                json={"username": username, "password": "pass123"},
                timeout=5
            )
            print(f"Status: {response.status_code}")
            print(f"Token received: {response.json()['access_token'][:50]}...")
            
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Create listing
            print_section("4. Creating a Listing")
            listing_data = {
                "title": "Vintage Camera",
                "price": {"amount": 299.99, "currency": "USD"},
                "condition": {
                    "score": 8,
                    "detailed_description": "Good condition",
                    "known_defects": ["Small scratch"]
                },
                "attributes": [
                    {"key": "brand", "value": "Canon"},
                    {"key": "model", "value": "AE-1"}
                ]
            }
            response = requests.post(
                f"{BASE_URL}/listings",
                json=listing_data,
                headers=headers,
                timeout=5
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                listing = response.json()
                print(f"Created listing ID: {listing['listing_id']}")
                print(f"Title: {listing['title']}")
                print(f"Price: {listing['price']['amount']} {listing['price']['currency']}")
                
                listing_id = listing['listing_id']
                
                # Get listing
                print_section("5. Getting Listing Details")
                response = requests.get(
                    f"{BASE_URL}/listings/{listing_id}",
                    headers=headers,
                    timeout=5
                )
                print(f"Status: {response.status_code}")
                print(f"Listing: {response.json()['title']}")
                
                # Search
                print_section("6. Searching for 'camera'")
                response = requests.get(
                    f"{BASE_URL}/search?query=camera&min_relevance=0.5",
                    headers=headers,
                    timeout=5
                )
                print(f"Status: {response.status_code}")
                results = response.json()
                print(f"Found {len(results)} results")
                
                print_section("Demo Completed Successfully! ✓")
                return True
        else:
            print(f"Registration failed: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Wait for server to be ready
    print("Waiting for server to be ready...")
    time.sleep(3)
    
    # Test if server is accessible
    max_retries = 5
    for i in range(max_retries):
        try:
            requests.get("http://localhost:8000/health", timeout=2)
            print("✓ Server is ready!\n")
            break
        except:
            if i < max_retries - 1:
                print(f"Server not ready, retrying ({i+1}/{max_retries})...")
                time.sleep(2)
            else:
                print("✗ Server is not accessible. Please start the server first.")
                sys.exit(1)
    
    # Run tests
    success = test_api()
    
    if success:
        print("\n" + "="*60)
        print("  Access the API documentation at:")
        print("  - Swagger UI: http://localhost:8000/docs")
        print("  - ReDoc: http://localhost:8000/redoc")
        print("="*60)
