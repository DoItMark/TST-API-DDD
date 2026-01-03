# Testing Documentation

## Table of Contents
- [What is TDD?](#what-is-tdd)
- [What is CI/CD?](#what-is-cicd)
- [Running Tests Locally](#running-tests-locally)
- [Writing Tests with TDD](#writing-tests-with-tdd)
- [Reading Coverage Reports](#reading-coverage-reports)
- [Interpreting CI/CD Results](#interpreting-cicd-results)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## What is TDD?

**Test-Driven Development (TDD)** is a software development approach where you write tests before writing the actual code.

### TDD Cycle (Red-Green-Refactor):
1. **Red**: Write a failing test that defines a desired improvement or new function
2. **Green**: Write the minimum code necessary to make the test pass
3. **Refactor**: Clean up the code while keeping tests passing

### Benefits of TDD:
- ✅ **Better Code Quality**: Forces you to think about design before implementation
- ✅ **Comprehensive Coverage**: Ensures all features are tested
- ✅ **Living Documentation**: Tests serve as examples of how to use the code
- ✅ **Regression Prevention**: Catches bugs early when changing code
- ✅ **Confidence**: Easier to refactor knowing tests will catch issues

### AAA Pattern (Arrange-Act-Assert):
Our tests follow the AAA pattern:
```python
def test_register_user_success(client):
    # Arrange: Set up test data
    user_data = {"username": "testuser", "password": "testpass123"}
    
    # Act: Execute the function being tested
    response = client.post("/register", json=user_data)
    
    # Assert: Verify the result
    assert response.status_code == 201
    assert "user_id" in response.json()
```

---

## What is CI/CD?

**Continuous Integration/Continuous Deployment (CI/CD)** is a practice that automates testing and deployment.

### Continuous Integration (CI):
- Automatically runs tests when code is pushed
- Ensures new code doesn't break existing functionality
- Provides immediate feedback to developers
- Tests on multiple Python versions (3.11, 3.12, 3.13)

### How Our CI Pipeline Works:
1. **Trigger**: Runs on every push and pull request to main branch
2. **Setup**: Installs Python and dependencies
3. **Test**: Runs all tests with pytest
4. **Coverage**: Generates coverage reports
5. **Report**: Displays results in GitHub Actions UI
6. **Pass/Fail**: Marks the build as successful or failed

### GitHub Actions Workflow:
Our `.github/workflows/ci.yml` defines the pipeline:
- Tests on Python 3.11, 3.12, and 3.13
- Uses pip caching for faster builds
- Runs pytest with coverage
- Fails if coverage is below 80%
- Uploads coverage reports as artifacts

---

## Running Tests Locally

### Prerequisites:
1. Python 3.11+ installed
2. Virtual environment (recommended)

### Setup:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Running All Tests:
```bash
# Run all tests with coverage
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage report
pytest --cov=listing_api --cov-report=term-missing
```

### Running Specific Tests:
```bash
# Run tests in a specific file
pytest test_listing_api.py

# Run a specific test class
pytest test_listing_api.py::TestAuthentication

# Run a specific test function
pytest test_listing_api.py::TestAuthentication::test_register_user_success

# Run tests with a specific marker
pytest -m auth          # Run authentication tests
pytest -m listings      # Run listing tests
pytest -m security      # Run security tests
pytest -m search        # Run search tests
```

### Running Tests in Watch Mode:
```bash
# Install pytest-watch (optional)
pip install pytest-watch

# Run tests automatically when files change
ptw
```

---

## Writing Tests with TDD

### Step 1: Write a Failing Test
```python
def test_new_feature(client):
    """Test description of what should happen"""
    # Arrange
    data = {"key": "value"}
    
    # Act
    response = client.post("/new-endpoint", json=data)
    
    # Assert
    assert response.status_code == 201
```

### Step 2: Run the Test (It Should Fail)
```bash
pytest test_listing_api.py::test_new_feature
```

### Step 3: Implement the Feature
```python
# In listing_api.py
@app.post("/new-endpoint")
async def new_endpoint(data: dict):
    # Implementation
    return {"status": "success"}
```

### Step 4: Run the Test Again (It Should Pass)
```bash
pytest test_listing_api.py::test_new_feature
```

### Step 5: Refactor (If Needed)
Clean up code while keeping tests passing.

### Test Naming Convention:
```python
# Good test names are descriptive
test_register_user_success()
test_register_user_duplicate_username_fails()
test_create_listing_without_auth_fails()

# Bad test names are vague
test_register()
test_1()
test_user()
```

### Using Fixtures:
```python
# Fixtures help with test setup
@pytest.fixture
def sample_data():
    """Reusable test data"""
    return {"username": "test", "password": "pass123"}

def test_with_fixture(client, sample_data):
    response = client.post("/register", json=sample_data)
    assert response.status_code == 201
```

---

## Reading Coverage Reports

### Terminal Report:
```bash
pytest --cov=listing_api --cov-report=term-missing
```

Output shows:
```
Name              Stmts   Miss  Cover   Missing
-----------------------------------------------
listing_api.py      250      5    98%   45-47
-----------------------------------------------
TOTAL              250      5    98%
```

- **Stmts**: Total statements in the file
- **Miss**: Statements not covered by tests
- **Cover**: Coverage percentage
- **Missing**: Line numbers not covered

### HTML Report:
```bash
pytest --cov=listing_api --cov-report=html
```

Then open `htmlcov/index.html` in your browser:
- Interactive report with highlighted code
- Shows which lines are covered (green) and which aren't (red)
- Click on files to see detailed line-by-line coverage

### Coverage Goals:
- ✅ **80%+**: Minimum acceptable coverage (enforced by CI)
- ✅ **90%+**: Good coverage
- ✅ **95%+**: Excellent coverage

### What to Cover:
- ✅ All API endpoints
- ✅ Authentication and authorization
- ✅ Business logic
- ✅ Error handling
- ✅ Edge cases

### What NOT to Cover:
- ❌ Third-party library code
- ❌ Configuration files
- ❌ Scripts like `convert_to_pdf.py`

---

## Interpreting CI/CD Results

### Viewing Results:
1. Go to your GitHub repository
2. Click on "Actions" tab
3. Click on the latest workflow run
4. View test results for each Python version

### Successful Build:
- ✅ Green checkmark
- All tests passed
- Coverage above 80%
- Ready to merge

### Failed Build:
- ❌ Red X
- Check the logs to see which test failed
- Fix the issue and push again

### Pull Request Checks:
When you open a PR, you'll see:
```
✅ CI/CD Pipeline / test (3.11)
✅ CI/CD Pipeline / test (3.12)
✅ CI/CD Pipeline / test (3.13)
```

All must pass before merging.

### Downloading Coverage Reports:
1. Go to the failed/successful workflow run
2. Scroll to "Artifacts" section
3. Download `coverage-report-{python-version}`
4. Extract and open `htmlcov/index.html`

---

## Best Practices

### Test Independence:
```python
# Good: Each test is independent
def test_create_user(client):
    response = client.post("/register", json={"username": "user1", "password": "pass"})
    assert response.status_code == 201

def test_login_user(client):
    # Setup within the test
    client.post("/register", json={"username": "user2", "password": "pass"})
    response = client.post("/login", json={"username": "user2", "password": "pass"})
    assert response.status_code == 200

# Bad: Second test depends on first test
def test_create_user(client):
    global user_id
    response = client.post("/register", json={"username": "user", "password": "pass"})
    user_id = response.json()["user_id"]

def test_use_user(client):
    # Depends on global variable from previous test
    response = client.get(f"/users/{user_id}")
```

### Test Both Happy and Sad Paths:
```python
# Happy path (success case)
def test_login_with_correct_credentials(client):
    # Test should pass

# Sad path (error case)
def test_login_with_wrong_password(client):
    # Test should handle error correctly
```

### Use Descriptive Assertions:
```python
# Good: Clear what's being tested
assert response.status_code == 201
assert "user_id" in response.json()
assert response.json()["username"] == "testuser"

# Bad: Vague assertions
assert response
assert data
```

### Test Organization:
```python
# Organize tests by feature using classes
class TestAuthentication:
    """All auth-related tests"""
    def test_register(self): pass
    def test_login(self): pass

class TestListings:
    """All listing-related tests"""
    def test_create_listing(self): pass
    def test_get_listing(self): pass
```

### Use Markers:
```python
# Mark tests by category
@pytest.mark.auth
def test_register(): pass

@pytest.mark.security
def test_unauthorized_access(): pass

# Run only marked tests
pytest -m auth
pytest -m security
```

---

## Troubleshooting

### Issue: Tests fail with "ModuleNotFoundError"
**Solution:**
```bash
# Make sure you're in the right directory
cd /path/to/TST-API-DDD

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Issue: Tests pass locally but fail in CI
**Possible causes:**
1. **Python version difference**: CI tests on 3.11, 3.12, 3.13
   - Test locally with different Python versions
2. **Missing dependency**: Check `requirements.txt` and `requirements-dev.txt`
3. **Environment variables**: CI doesn't have your local `.env` file
   - Use default values or GitHub Secrets

### Issue: Coverage is below 80%
**Solution:**
```bash
# See which lines aren't covered
pytest --cov=listing_api --cov-report=term-missing

# Or generate HTML report
pytest --cov=listing_api --cov-report=html
# Open htmlcov/index.html to see missing lines

# Add tests for uncovered lines
```

### Issue: Test database not clearing between tests
**Solution:**
Our `clear_databases` fixture (with `autouse=True`) should handle this:
```python
@pytest.fixture(autouse=True)
def clear_databases():
    """Automatically clear databases before each test"""
    listings_db.clear()
    search_index_db.clear()
    users_db.clear()
    yield
    # Cleanup after test
```

### Issue: Slow tests
**Solutions:**
- Use fixtures to avoid repeating setup
- Run specific tests instead of full suite
- Use pytest-xdist for parallel testing:
  ```bash
  pip install pytest-xdist
  pytest -n auto  # Run tests in parallel
  ```

### Issue: Authentication tests failing
**Common causes:**
1. Token expired - Tests should create fresh tokens
2. Database not cleared - Check `clear_databases` fixture
3. User already exists - Tests should use unique usernames

### Issue: CI/CD workflow not triggering
**Check:**
1. Workflow file is in `.github/workflows/ci.yml`
2. File is valid YAML (indentation matters!)
3. Branch name is correct (main vs master)
4. Push includes the workflow file

### Getting Help:
1. Check test output for specific error messages
2. Use `pytest -v` for verbose output
3. Use `pytest --pdb` to debug failing tests
4. Check GitHub Actions logs for CI failures
5. Review this documentation for best practices

---

## Additional Resources

### Pytest Documentation:
- [Official Pytest Docs](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Markers](https://docs.pytest.org/en/stable/mark.html)

### FastAPI Testing:
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [TestClient Documentation](https://fastapi.tiangolo.com/reference/testclient/)

### GitHub Actions:
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Python GitHub Actions](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)

---

## Quick Reference

### Common Commands:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=listing_api

# Run specific test
pytest test_listing_api.py::test_name

# Run tests with marker
pytest -m auth

# Run in verbose mode
pytest -v

# Stop at first failure
pytest -x

# Show local variables in tracebacks
pytest -l
```

### Test Structure:
```python
def test_description(client, fixtures):
    """Clear docstring explaining what this tests"""
    # Arrange: Setup
    data = {...}
    
    # Act: Execute
    response = client.post("/endpoint", json=data)
    
    # Assert: Verify
    assert response.status_code == 200
```

### Coverage Goals:
- Minimum: 80%
- Good: 90%+
- Excellent: 95%+

---

**Happy Testing! 🎉**
