# Testing Guide for Item Management API

This comprehensive guide covers everything you need to know about testing, Test-Driven Development (TDD), and Continuous Integration/Continuous Deployment (CI/CD) for the Item Management API project.

---

## Table of Contents

1. [What is TDD?](#1-what-is-tdd)
2. [What is CI/CD?](#2-what-is-cicd)
3. [Running Tests Locally](#3-running-tests-locally)
4. [Writing Tests with TDD](#4-writing-tests-with-tdd)
5. [Reading Coverage Reports](#5-reading-coverage-reports)
6. [Interpreting CI/CD Results](#6-interpreting-cicd-results)
7. [Best Practices](#7-best-practices)
8. [Troubleshooting](#8-troubleshooting)
9. [Additional Resources](#9-additional-resources)
10. [Quick Reference](#10-quick-reference)

---

## 1. What is TDD?

### Definition

**Test-Driven Development (TDD)** is a software development approach where you write tests *before* writing the actual code. This might seem backward at first, but it's a powerful technique that leads to better-designed, more reliable code.

### Benefits of TDD

1. **Better Code Quality**: Writing tests first forces you to think about the requirements and design before implementation
2. **Fewer Bugs**: Tests catch issues early in the development process
3. **Confidence to Refactor**: With comprehensive tests, you can refactor code safely
4. **Living Documentation**: Tests serve as documentation showing how the code should work
5. **Faster Development**: While it seems slower initially, TDD actually speeds up development by reducing debugging time

### The Red-Green-Refactor Cycle

TDD follows a simple three-step cycle:

```
1. 🔴 RED: Write a failing test
   └─> Write a test for a feature that doesn't exist yet
   
2. 🟢 GREEN: Make the test pass
   └─> Write the minimum code necessary to make the test pass
   
3. 🔵 REFACTOR: Improve the code
   └─> Clean up the code while keeping tests passing
```

#### Example of Red-Green-Refactor

**Step 1 - RED: Write a failing test**

```python
def test_register_user_successfully(client, sample_user_data):
    """Test successful user registration"""
    # Arrange
    user_data = sample_user_data
    
    # Act
    response = client.post("/register", json=user_data)
    
    # Assert
    assert response.status_code == 201
    assert "user_id" in response.json()
```

At this point, the endpoint doesn't exist yet, so the test fails. ❌

**Step 2 - GREEN: Make the test pass**

```python
@app.post("/register", status_code=201)
async def register_user(user_data: UserCreate):
    user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password)
    )
    users_db[user.username] = user
    return {"user_id": str(user.user_id)}
```

Now the test passes! ✅

**Step 3 - REFACTOR: Improve the code**

```python
@app.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """Register a new user with validation"""
    if user_data.username in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password)
    )
    users_db[user.username] = user
    
    return {
        "message": "User registered successfully",
        "user_id": str(user.user_id),
        "seller_id": str(user.seller_id)
    }
```

The code is now cleaner, more robust, and the test still passes! ✨

### The AAA Pattern

Every test should follow the **AAA pattern**:

1. **Arrange**: Set up the test data and conditions
2. **Act**: Execute the code being tested
3. **Assert**: Verify the results

```python
def test_create_listing_with_valid_data(client, sample_listing_data, auth_headers):
    """Test creating a listing with valid data"""
    
    # ARRANGE - Set up test data
    listing_data = sample_listing_data
    
    # ACT - Execute the operation
    response = client.post("/listings", json=listing_data, headers=auth_headers)
    
    # ASSERT - Verify the results
    assert response.status_code == 201
    assert data["title"] == listing_data["title"]
    assert "listing_id" in data
```

This pattern makes tests easy to read and understand.

---

## 2. What is CI/CD?

### What is Continuous Integration (CI)?

**Continuous Integration** is the practice of automatically testing code every time changes are pushed to the repository. Instead of waiting to test until the end, CI runs tests constantly.

**Benefits:**
- Catch bugs early, before they reach production
- Ensure code works across different Python versions
- Prevent breaking changes from being merged
- Maintain code quality standards

### What is Continuous Deployment (CD)?

**Continuous Deployment** is the practice of automatically deploying code that passes all tests. In this project, we focus on the CI part, but CD can be added later.

### How Our GitHub Actions Pipeline Works

Our CI/CD pipeline is defined in `.github/workflows/ci.yml`. Here's what happens:

```yaml
on:
  push:
    branches: [ main ]      # Runs when code is pushed to main
  pull_request:
    branches: [ main ]      # Runs when a PR is created targeting main
```

#### Pipeline Stages

1. **Trigger**: Pipeline starts when you push code or create a PR
2. **Matrix Build**: Tests run on Python 3.11, 3.12, and 3.13 simultaneously
3. **Checkout Code**: GitHub downloads your code
4. **Setup Python**: Installs the specified Python version
5. **Cache Dependencies**: Speeds up builds by caching pip packages
6. **Install Dependencies**: Installs all required packages
7. **Run Tests**: Executes all tests with coverage measurement
8. **Display Coverage**: Shows how much code is tested
9. **Upload Artifacts**: Saves HTML coverage reports
10. **Enforce Threshold**: Fails if coverage is below 80%

#### Visual Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  Developer pushes code or creates Pull Request              │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  GitHub Actions triggers CI/CD pipeline                     │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ├──────────────┬──────────────┬────────────┐
                    ▼              ▼              ▼            │
            ┌──────────────┐ ┌──────────┐ ┌──────────┐        │
            │ Python 3.11  │ │ Py 3.12  │ │ Py 3.13  │        │
            └──────┬───────┘ └────┬─────┘ └────┬─────┘        │
                   │              │            │              │
                   ├──────────────┴────────────┘              │
                   ▼                                          │
            ┌─────────────────┐                               │
            │ Run all tests   │                               │
            │ with coverage   │                               │
            └────────┬────────┘                               │
                     │                                         │
                     ▼                                         │
            ┌─────────────────┐                               │
            │  All tests      │                               │
            │  pass? ✅       │                               │
            └────────┬────────┘                               │
                     │                                         │
                     ▼                                         │
            ┌─────────────────┐                               │
            │ Coverage >= 80%?│                               │
            │  ✅              │                               │
            └────────┬────────┘                               │
                     │                                         │
                     ▼                                         │
            ┌─────────────────┐                               │
            │ ✨ BUILD SUCCESS │                              │
            └─────────────────┘                               │
```

---

## 3. Running Tests Locally

### Prerequisites

Before running tests, make sure you have:

1. **Python 3.11 or higher** installed
   ```bash
   python --version
   ```

2. **Virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Dependencies installed**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

### Running All Tests

To run all tests:

```bash
pytest
```

This will:
- Run all test files matching `test_*.py`
- Show verbose output (`-v` flag)
- Generate coverage report
- Display missing coverage lines
- Create an HTML coverage report in `htmlcov/`

### Running Specific Tests

#### Run a specific test file

```bash
pytest test_listing_api.py
```

#### Run a specific test class

```bash
pytest test_listing_api.py::TestAuthentication
```

#### Run a specific test function

```bash
pytest test_listing_api.py::TestAuthentication::test_register_user_successfully
```

#### Run tests with a specific marker

```bash
# Run only authentication tests
pytest -m auth

# Run only listing tests
pytest -m listings

# Run only security tests
pytest -m security

# Run only search tests
pytest -m search
```

#### Run tests matching a pattern

```bash
# Run all tests with "register" in the name
pytest -k register

# Run all tests with "listing" but not "delete"
pytest -k "listing and not delete"
```

### Watch Mode (Re-run on Changes)

For continuous testing during development, you can use `pytest-watch`:

```bash
# Install pytest-watch
pip install pytest-watch

# Run tests automatically when files change
ptw
```

### Verbose Output

For more detailed output:

```bash
# Show print statements
pytest -s

# Show extra test summary info
pytest -v

# Show locals in tracebacks
pytest -l
```

---

## 4. Writing Tests with TDD

### 5-Step TDD Process

Follow these steps when adding a new feature:

**Step 1: Write a test for the feature**

```python
def test_update_listing_price_as_owner(client, sample_listing_data, auth_headers):
    """Test updating listing price as owner"""
    # This test will fail because the endpoint doesn't exist yet
    create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
    listing_id = create_response.json()["listing_id"]
    
    new_price = {"new_price": {"amount": "150.00", "currency": "USD"}}
    response = client.patch(f"/listings/{listing_id}/price", json=new_price, headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json()["price"]["amount"] == "150.00"
```

**Step 2: Run the test and watch it fail**

```bash
pytest test_listing_api.py::test_update_listing_price_as_owner
# Expected: FAILED ❌
```

**Step 3: Write the minimum code to make it pass**

```python
@app.patch("/listings/{listing_id}/price", response_model=ListingResponse)
async def update_listing_price(
    listing_id: UUID,
    request: UpdatePriceRequest,
    current_user: User = Depends(get_current_user)
):
    listing = listings_db[listing_id]
    listing.update_price(request.new_price)
    return listing
```

**Step 4: Run the test again**

```bash
pytest test_listing_api.py::test_update_listing_price_as_owner
# Expected: PASSED ✅
```

**Step 5: Refactor and add validation**

```python
@app.patch("/listings/{listing_id}/price", response_model=ListingResponse)
async def update_listing_price(
    listing_id: UUID,
    request: UpdatePriceRequest,
    current_user: User = Depends(get_current_user)
):
    """Update listing price (requires authentication)"""
    if listing_id not in listings_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing {listing_id} not found"
        )
    
    listing = listings_db[listing_id]
    
    # Check ownership
    if listing.seller_id != current_user.seller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update price of your own listings"
        )
    
    listing.update_price(request.new_price)
    return listing
```

### Test Naming Conventions

Good test names are descriptive and follow a pattern:

```python
# ✅ GOOD: Describes what's being tested and expected outcome
def test_register_user_successfully()
def test_register_duplicate_username_fails()
def test_create_listing_without_authentication_fails()
def test_update_listing_price_as_non_owner_fails()

# ❌ BAD: Vague, doesn't describe the scenario
def test_register()
def test_listing()
def test_update()
```

**Pattern**: `test_<action>_<scenario>_<expected_result>`

### Using Fixtures

Fixtures provide reusable test data and setup:

```python
@pytest.fixture
def client():
    """Provides a FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def sample_user_data():
    """Provides sample user data"""
    return {
        "username": "testuser",
        "password": "testpass123"
    }

@pytest.fixture
def registered_user(client, sample_user_data):
    """Creates a registered user and returns user data"""
    response = client.post("/register", json=sample_user_data)
    return {**sample_user_data, **response.json()}

@pytest.fixture
def auth_headers(client, registered_user):
    """Provides authentication headers"""
    response = client.post("/login", json={
        "username": registered_user["username"],
        "password": registered_user["password"]
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

**Using fixtures in tests:**

```python
def test_create_listing_with_valid_data(client, sample_listing_data, auth_headers):
    # client, sample_listing_data, and auth_headers are automatically provided
    response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
    assert response.status_code == 201
```

### Example: Complete TDD Cycle

Let's implement a feature to get listing by ID using TDD:

**1. Write the test first (RED 🔴)**

```python
def test_get_listing_by_id(client, sample_listing_data, auth_headers):
    """Test getting a listing by ID"""
    # Create a listing
    create_response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
    listing_id = create_response.json()["listing_id"]
    
    # Try to get it
    response = client.get(f"/listings/{listing_id}")
    
    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["listing_id"] == listing_id
    assert data["title"] == sample_listing_data["title"]
```

**2. Run test - it fails (RED 🔴)**

```bash
pytest test_listing_api.py::test_get_listing_by_id -v
# FAILED: 404 NOT FOUND - endpoint doesn't exist
```

**3. Implement minimal code (GREEN 🟢)**

```python
@app.get("/listings/{listing_id}", response_model=ListingResponse)
async def get_listing(listing_id: UUID):
    """Get a listing by ID"""
    return listings_db[listing_id]
```

**4. Run test - it passes (GREEN 🟢)**

```bash
pytest test_listing_api.py::test_get_listing_by_id -v
# PASSED ✅
```

**5. Refactor and add edge case test (REFACTOR 🔵)**

Add test for non-existent listing:

```python
def test_get_nonexistent_listing_returns_404(client):
    """Test getting non-existent listing returns 404"""
    nonexistent_id = uuid4()
    response = client.get(f"/listings/{nonexistent_id}")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
```

Update implementation:

```python
@app.get("/listings/{listing_id}", response_model=ListingResponse)
async def get_listing(listing_id: UUID):
    """Get a listing by ID"""
    if listing_id not in listings_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing {listing_id} not found"
        )
    return listings_db[listing_id]
```

**6. Run all tests - they pass (GREEN 🟢)**

```bash
pytest test_listing_api.py -v
# All tests PASSED ✅
```

---

## 5. Reading Coverage Reports

### What is Code Coverage?

**Code coverage** measures how much of your code is executed during tests. It's expressed as a percentage:

```
Coverage = (Lines executed during tests / Total lines of code) × 100
```

### Terminal Coverage Report

When you run `pytest`, you'll see a coverage report like this:

```
---------- coverage: platform linux, python 3.11.0 -----------
Name              Stmts   Miss  Cover   Missing
-----------------------------------------------
listing_api.py      250     15    94%   125-127, 234-236, 445
-----------------------------------------------
TOTAL               250     15    94%
```

**Understanding the columns:**

- **Name**: File being tested
- **Stmts**: Total number of executable statements
- **Miss**: Number of statements not covered by tests
- **Cover**: Coverage percentage
- **Missing**: Line numbers not covered

### HTML Coverage Report

For a more detailed view, open `htmlcov/index.html` in your browser:

```bash
# Generate and open HTML report
pytest
open htmlcov/index.html  # On Mac
# On Linux: xdg-open htmlcov/index.html
# On Windows: start htmlcov/index.html
```

The HTML report shows:
- **Color-coded lines**: Green (covered), red (not covered)
- **Branch coverage**: Whether all if/else paths are tested
- **Per-file breakdown**: Coverage for each file

### Coverage Goals

Different projects have different coverage standards:

| Coverage | Interpretation | Action |
|----------|----------------|---------|
| 0-50%    | ❌ Poor        | Critical - add tests immediately |
| 50-70%   | ⚠️ Fair        | Needs improvement |
| 70-80%   | 👍 Good        | Keep adding tests |
| 80-90%   | ✨ Very Good   | Excellent coverage |
| 90-95%   | 🎯 Excellent   | Professional level |
| 95-100%  | 🏆 Outstanding | Exceptional (may have diminishing returns) |

**Our project targets:**
- **Minimum**: 80% (enforced by CI)
- **Target**: 90%+
- **Ideal**: 94%+ (achieved in PR #4)

### What to Cover vs What Not to Cover

**✅ DO Cover:**
- Business logic and calculations
- API endpoints and request handling
- Error handling and edge cases
- Authentication and authorization
- Data validation
- Database operations

**❌ DON'T Need to Cover:**
- Third-party library code
- Configuration files
- `if __name__ == "__main__":` blocks
- Simple property getters/setters
- Obvious one-liners

### Interpreting Missing Coverage

Example missing lines:

```python
# listing_api.py lines 125-127 not covered
def _calculate_complex_score(self):
    if self.condition.score > 8:
        return self.price.amount * 1.5  # ❌ Not tested
    return self.price.amount
```

**How to fix:**

```python
def test_calculate_complex_score_high_condition():
    """Test score calculation for high condition items"""
    listing = create_listing_with_condition_score(9)
    score = listing._calculate_complex_score()
    assert score == listing.price.amount * 1.5  # ✅ Now tested
```

---

## 6. Interpreting CI/CD Results

### Viewing Results in GitHub Actions

1. **Go to your repository on GitHub**
2. **Click the "Actions" tab**
3. **Select a workflow run** from the list
4. **View job details** by clicking on a job

### Understanding Pass/Fail Status

#### ✅ All Checks Passed

```
✓ test (3.11) — 2m 34s
✓ test (3.12) — 2m 28s
✓ test (3.13) — 2m 31s
```

**Meaning**: All tests passed on all Python versions
**Action**: You can safely merge the PR

#### ❌ Some Checks Failed

```
✓ test (3.11) — 2m 34s
✗ test (3.12) — 1m 12s  ← Failed here
✓ test (3.13) — 2m 31s
```

**Meaning**: Tests failed on Python 3.12
**Action**: Click on the failed job to see error details

### Reading Job Logs

Click on a failed job to see logs:

```
Run tests with coverage
  pytest --cov=listing_api --cov-report=term-missing

======================== test session starts ========================
platform linux -- Python 3.12.0, pytest-8.3.4

test_listing_api.py::TestAuthentication::test_login_with_correct_credentials FAILED

======================== FAILURES ===================================
___________ TestAuthentication.test_login_with_correct_credentials ___________

    def test_login_with_correct_credentials(client, registered_user):
>       response = client.post("/login", json=login_data)
E       AssertionError: assert 500 == 200

test_listing_api.py:142: AssertionError
======================== short test summary info ====================
FAILED test_listing_api.py::TestAuthentication::test_login_with_correct_credentials - AssertionError
```

**How to interpret:**
1. **Test name**: `test_login_with_correct_credentials` failed
2. **Line number**: `test_listing_api.py:142`
3. **Error**: Expected status code 200, got 500
4. **Action**: Fix the login endpoint or the test

### Pull Request Checks

When you create a PR, you'll see checks at the bottom:

```
Checks
  ✓ CI/CD Pipeline / test (3.11) — Required
  ✓ CI/CD Pipeline / test (3.12) — Required
  ✓ CI/CD Pipeline / test (3.13) — Required
  
  All checks have passed
  [Merge pull request] button is enabled
```

### Downloading Coverage Artifacts

To download coverage reports from CI:

1. **Go to the workflow run**
2. **Scroll to "Artifacts" section**
3. **Download** `coverage-report-py3.11` (or other versions)
4. **Unzip and open** `htmlcov/index.html`

This lets you view the exact coverage report from CI, even if you can't reproduce the issue locally.

---

## 7. Best Practices

### Test Independence

**Each test should be completely independent** and not rely on other tests:

```python
# ❌ BAD: Tests depend on order
def test_1_create_user():
    client.post("/register", json=user_data)

def test_2_login_user():  # Depends on test_1
    client.post("/login", json=user_data)

# ✅ GOOD: Each test is independent
def test_create_user(client, sample_user_data):
    response = client.post("/register", json=sample_user_data)
    assert response.status_code == 201

def test_login_user(client, registered_user):  # Uses fixture
    login_data = {"username": registered_user["username"], "password": registered_user["password"]}
    response = client.post("/login", json=login_data)
    assert response.status_code == 200
```

### Test Both Happy and Sad Paths

**Happy path**: Things work as expected
**Sad path**: Things go wrong

```python
# ✅ Happy path
def test_create_listing_with_valid_data(client, sample_listing_data, auth_headers):
    response = client.post("/listings", json=sample_listing_data, headers=auth_headers)
    assert response.status_code == 201

# ✅ Sad path
def test_create_listing_without_authentication_fails(client, sample_listing_data):
    response = client.post("/listings", json=sample_listing_data)
    assert response.status_code == 403
```

### Use Descriptive Assertions

```python
# ❌ BAD: Unclear what went wrong
assert response.status_code == 200

# ✅ GOOD: Clear error message
assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"

# ✅ EVEN BETTER: Use specific checks
assert response.status_code == 200
assert "listing_id" in response.json()
assert response.json()["title"] == "Expected Title"
```

### Organize Tests Logically

Use test classes to group related tests:

```python
class TestAuthentication:
    """All authentication-related tests"""
    
    def test_register_user_successfully(self):
        pass
    
    def test_login_with_correct_credentials(self):
        pass

class TestListingOperations:
    """All listing CRUD tests"""
    
    def test_create_listing(self):
        pass
    
    def test_update_listing(self):
        pass
```

### Use Markers for Test Organization

```python
@pytest.mark.auth
def test_register_user():
    pass

@pytest.mark.listings
@pytest.mark.security
def test_update_listing_as_non_owner_fails():
    pass
```

Run specific groups:

```bash
pytest -m auth              # Run only auth tests
pytest -m "auth or security"  # Run auth or security tests
pytest -m "not slow"        # Skip slow tests
```

### Keep Tests Fast

- Use in-memory databases (like we do)
- Mock external API calls
- Avoid unnecessary sleeps
- Use fixtures to share setup

```python
# ❌ SLOW: Creates user in every test
def test_create_listing():
    user = client.post("/register", json=user_data)
    token = client.post("/login", json=user_data).json()["access_token"]
    # ... rest of test

# ✅ FAST: Uses fixture
def test_create_listing(auth_headers):  # Fixture handles setup
    # ... test immediately
```

---

## 8. Troubleshooting

### Common Issues and Solutions

#### Issue: `ModuleNotFoundError: No module named 'listing_api'`

**Problem**: Python can't find the module to test.

**Solutions**:

```bash
# Solution 1: Run from project root
cd /path/to/TST-API-DDD
pytest

# Solution 2: Install in development mode
pip install -e .

# Solution 3: Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

---

#### Issue: Tests Pass Locally But Fail in CI

**Problem**: Tests work on your machine but fail in GitHub Actions.

**Common causes and solutions**:

1. **Different Python versions**
   ```bash
   # Test with multiple Python versions locally
   pyenv install 3.11 3.12 3.13
   pyenv local 3.11 3.12 3.13
   ```

2. **Missing dependencies**
   ```bash
   # Ensure requirements-dev.txt is up to date
   pip freeze > requirements-check.txt
   diff requirements-dev.txt requirements-check.txt
   ```

3. **Time zone differences**
   ```python
   # ❌ BAD: Assumes local time zone
   created_at = datetime.now()
   
   # ✅ GOOD: Use UTC explicitly
   created_at = datetime.utcnow()
   ```

4. **Database not clearing between tests**
   ```python
   # ✅ GOOD: Use autouse fixture
   @pytest.fixture(autouse=True)
   def clear_databases():
       listings_db.clear()
       users_db.clear()
       yield
       listings_db.clear()
       users_db.clear()
   ```

---

#### Issue: Coverage Below Threshold

**Problem**: CI fails with "Coverage below 80%"

**Solution**:

```bash
# 1. Check which lines are missing coverage
pytest --cov=listing_api --cov-report=term-missing

# 2. Open HTML report to see details
pytest
open htmlcov/index.html

# 3. Add tests for uncovered lines
# Focus on red lines in the HTML report
```

---

#### Issue: Database Not Clearing Between Tests

**Problem**: Tests interfere with each other.

**Solution**:

```python
# ✅ Use autouse=True to automatically clear before each test
@pytest.fixture(autouse=True)
def clear_databases():
    """Auto-clear databases before and after each test"""
    listings_db.clear()
    search_index_db.clear()
    users_db.clear()
    yield
    listings_db.clear()
    search_index_db.clear()
    users_db.clear()
```

---

#### Issue: Slow Tests

**Problem**: Tests take too long to run.

**Solutions**:

```bash
# 1. Identify slow tests
pytest --durations=10

# 2. Run tests in parallel
pip install pytest-xdist
pytest -n auto  # Uses all CPU cores

# 3. Skip slow tests during development
@pytest.mark.slow
def test_expensive_operation():
    pass

# Run without slow tests
pytest -m "not slow"
```

---

#### Issue: Authentication Failures in Tests

**Problem**: Tests fail with 401/403 errors.

**Solution**:

```python
# ✅ Use proper fixtures for authentication
@pytest.fixture
def auth_token(client, registered_user):
    """Get valid authentication token"""
    response = client.post("/login", json={
        "username": registered_user["username"],
        "password": registered_user["password"]
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]

@pytest.fixture
def auth_headers(auth_token):
    """Create proper authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}

# Use in tests
def test_protected_endpoint(client, auth_headers):
    response = client.post("/listings", json=data, headers=auth_headers)
    assert response.status_code == 201
```

---

#### Issue: CI Workflow Not Triggering

**Problem**: Pushed code but workflow doesn't run.

**Solutions**:

1. **Check workflow file syntax**
   ```bash
   # Validate YAML syntax
   yamllint .github/workflows/ci.yml
   ```

2. **Check branch name**
   ```yaml
   # Ensure you're pushing to correct branch
   on:
     push:
       branches: [ main ]  # Must match your branch name
   ```

3. **Check Actions are enabled**
   - Go to repository Settings → Actions → Allow all actions

4. **Check file location**
   ```
   .github/
     └── workflows/
         └── ci.yml  # Must be exactly this structure
   ```

---

## 9. Additional Resources

### Official Documentation

- **pytest**: https://docs.pytest.org/
  - Comprehensive testing framework documentation
  - Fixture reference
  - Plugin ecosystem

- **FastAPI Testing**: https://fastapi.tiangolo.com/tutorial/testing/
  - FastAPI-specific testing guide
  - TestClient usage
  - Dependency overrides

- **GitHub Actions**: https://docs.github.com/en/actions
  - Workflow syntax
  - Available actions
  - Secrets and variables

- **Coverage.py**: https://coverage.readthedocs.io/
  - Coverage measurement tool
  - Configuration options
  - Reporting formats

### Testing Best Practices

- **Martin Fowler - Test Pyramid**: https://martinfowler.com/articles/practical-test-pyramid.html
- **Google Testing Blog**: https://testing.googleblog.com/
- **pytest Good Practices**: https://docs.pytest.org/en/stable/goodpractices.html

### TDD Resources

- **Test-Driven Development by Kent Beck** (Book)
- **TDD Tutorial**: https://www.obeythetestinggoat.com/
- **Uncle Bob's TDD Rules**: http://butunclebob.com/ArticleS.UncleBob.TheThreeRulesOfTdd

### Video Tutorials

- **FastAPI Testing Tutorial** - YouTube search for latest
- **Python Testing with pytest** - Talk Python Training
- **GitHub Actions Tutorial** - GitHub official channel

---

## 10. Quick Reference

### Common Commands Cheat Sheet

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=listing_api

# Run specific test file
pytest test_listing_api.py

# Run specific test class
pytest test_listing_api.py::TestAuthentication

# Run specific test function
pytest test_listing_api.py::TestAuthentication::test_register_user_successfully

# Run tests with markers
pytest -m auth
pytest -m listings
pytest -m security
pytest -m search

# Run tests matching pattern
pytest -k "register"
pytest -k "listing and not delete"

# Verbose output
pytest -v

# Show print statements
pytest -s

# Show test durations
pytest --durations=10

# Run tests in parallel
pytest -n auto

# Generate HTML coverage report
pytest --cov=listing_api --cov-report=html
open htmlcov/index.html

# Check coverage threshold
coverage report --fail-under=80

# List all tests without running
pytest --collect-only
```

### Test Structure Template

```python
import pytest
from fastapi.testclient import TestClient
from listing_api import app

# Fixtures
@pytest.fixture
def client():
    return TestClient(app)

# Test class
class TestFeatureName:
    """Test description"""
    
    @pytest.mark.category
    def test_feature_happy_path(self, client, fixtures):
        """Test successful case"""
        # Arrange
        test_data = {"key": "value"}
        
        # Act
        response = client.post("/endpoint", json=test_data)
        
        # Assert
        assert response.status_code == 200
        assert "expected_key" in response.json()
    
    @pytest.mark.category
    def test_feature_sad_path(self, client):
        """Test failure case"""
        # Arrange
        invalid_data = {}
        
        # Act
        response = client.post("/endpoint", json=invalid_data)
        
        # Assert
        assert response.status_code == 400
```

### Coverage Goals Quick Reference

| Target | Interpretation | Action Required |
|--------|----------------|-----------------|
| 80%    | Minimum acceptable | Meet CI requirement |
| 90%    | Project target | Add more tests |
| 94%+   | Ideal (PR #4 level) | Excellent coverage |

### pytest Markers in This Project

```python
@pytest.mark.auth        # Authentication tests
@pytest.mark.listings    # Listing CRUD tests
@pytest.mark.security    # Security tests
@pytest.mark.search      # Search functionality tests
```

---

## Summary

This guide has covered:

1. ✅ **TDD fundamentals** - Red-Green-Refactor cycle and AAA pattern
2. ✅ **CI/CD concepts** - Automated testing and deployment
3. ✅ **Running tests** - Locally and with various options
4. ✅ **Writing tests** - Following TDD with practical examples
5. ✅ **Coverage reports** - Understanding and improving coverage
6. ✅ **CI/CD results** - Interpreting GitHub Actions output
7. ✅ **Best practices** - Writing maintainable, effective tests
8. ✅ **Troubleshooting** - Common issues and solutions
9. ✅ **Resources** - Where to learn more
10. ✅ **Quick reference** - Commands and templates

**Remember**: Good tests are an investment in your code's future. They give you confidence to make changes, catch bugs early, and serve as documentation for other developers.

Happy testing! 🎉
