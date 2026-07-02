import pytest

pytestmark = pytest.mark.django_db

def test_register_returns_201_with_valid_request(api_client):
    url = '/api/v1/auth/register/'
    payload = {
        "username": "newuser",
        "email": "newuser@test.com",
        "password": "StrongPassword123!",
        "full_name": "New User",
        "role": "STAFF" 
    }
    
    response = api_client.post(url, payload, format='json')
    
    assert response.status_code == 201
    assert 'id' in response.data

def test_register_returns_422_when_email_already_exists(api_client, admin_user):
    url = '/api/v1/auth/register/'
    payload = {
        "username": "anotheruser",
        "email": admin_user.email,
        "password": "StrongPassword123!",
        "full_name": "Another User",
        "role": "STAFF"
    }
    
    response = api_client.post(url, payload, format='json')
    
    # Your custom InvalidOperationException returns a 422 Unprocessable Entity
    assert response.status_code == 422 

def test_login_returns_200_with_valid_credentials(api_client, staff_user):
    url = '/api/v1/auth/login/'
    payload = {
        "email": staff_user.email,  # FIXED: Matches LoginSerializer contract
        "password": "TestPassword123!"
    }
    
    response = api_client.post(url, payload, format='json')
    
    assert response.status_code == 200
    assert 'access_token' in response.data
    assert 'refresh_token' in response.data

def test_login_returns_422_with_invalid_credentials(api_client, staff_user):
    url = '/api/v1/auth/login/'
    payload = {
        "email": staff_user.email,  # FIXED: Matches LoginSerializer contract
        "password": "WrongPassword!"
    }
    
    response = api_client.post(url, payload, format='json')
    
    assert response.status_code == 422

def test_refresh_token_returns_200_with_valid_refresh_token(api_client, staff_user):
    login_url = '/api/v1/auth/login/'
    login_payload = {
        "email": staff_user.email,  # FIXED: Matches LoginSerializer contract
        "password": "TestPassword123!"
    }
    login_response = api_client.post(login_url, login_payload, format='json')
    refresh_token = login_response.data.get('refresh_token')
    
    refresh_url = '/api/v1/auth/token/refresh/'
    refresh_payload = {
        "refresh": refresh_token 
    }
    
    response = api_client.post(refresh_url, refresh_payload, format='json')
    
    assert response.status_code == 200