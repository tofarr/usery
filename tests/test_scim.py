import asyncio
import json
import uuid
from typing import Dict, Any

import httpx

# Base URL for the API
BASE_URL = "http://localhost:8000"
SCIM_BASE_URL = f"{BASE_URL}/scim/v2"

# Test user credentials
TEST_USER = {
    "email": "admin@example.com",
    "username": "admin",
    "password": "password123",
}

# Test SCIM user
TEST_SCIM_USER = {
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
    "userName": f"scimuser_{uuid.uuid4().hex[:8]}",
    "name": {
        "formatted": "SCIM Test User"
    },
    "emails": [
        {
            "value": f"scimuser_{uuid.uuid4().hex[:8]}@example.com",
            "primary": True,
            "type": "work"
        }
    ],
    "active": True
}


async def get_token() -> str:
    """Get an access token for API authentication."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/auth/token",
            data={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"],
                "grant_type": "password",
                "scope": "openid profile email",
                "client_id": "usery",
            },
        )
        
        if response.status_code != 200:
            print(f"Failed to get token: {response.text}")
            raise Exception("Failed to get token")
        
        data = response.json()
        return data["access_token"]


async def test_service_provider_config(token: str) -> None:
    """Test the SCIM Service Provider Configuration endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SCIM_BASE_URL}/ServiceProviderConfig",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"Service Provider Config Status: {response.status_code}")
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.text}")


async def test_list_users(token: str) -> None:
    """Test the SCIM Users endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SCIM_BASE_URL}/Users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"List Users Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total Results: {data['totalResults']}")
            print(f"Users: {len(data['Resources'])}")
            if data['Resources']:
                print(f"First user: {json.dumps(data['Resources'][0], indent=2)}")
        else:
            print(f"Error: {response.text}")


async def test_create_user(token: str) -> Dict[str, Any]:
    """Test creating a user via SCIM."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SCIM_BASE_URL}/Users",
            headers={"Authorization": f"Bearer {token}"},
            json=TEST_SCIM_USER
        )
        
        print(f"Create User Status: {response.status_code}")
        if response.status_code == 201:
            user_data = response.json()
            print(f"Created user: {json.dumps(user_data, indent=2)}")
            return user_data
        else:
            print(f"Error: {response.text}")
            return {}


async def test_get_user(token: str, user_id: str) -> None:
    """Test getting a specific user via SCIM."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SCIM_BASE_URL}/Users/{user_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"Get User Status: {response.status_code}")
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.text}")


async def test_update_user(token: str, user_id: str) -> None:
    """Test updating a user via SCIM."""
    update_data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "name": {
            "formatted": "Updated SCIM Test User"
        },
        "active": True
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{SCIM_BASE_URL}/Users/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data
        )
        
        print(f"Update User Status: {response.status_code}")
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.text}")


async def test_patch_user(token: str, user_id: str) -> None:
    """Test patching a user via SCIM."""
    patch_data = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
        "Operations": [
            {
                "op": "replace",
                "path": "name.formatted",
                "value": "Patched SCIM Test User"
            }
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{SCIM_BASE_URL}/Users/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=patch_data
        )
        
        print(f"Patch User Status: {response.status_code}")
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.text}")


async def test_filter_users(token: str) -> None:
    """Test filtering users via SCIM."""
    filter_query = "userName sw \"scim\""
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SCIM_BASE_URL}/Users?filter={filter_query}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"Filter Users Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total Results: {data['totalResults']}")
            print(f"Users: {len(data['Resources'])}")
            if data['Resources']:
                print(f"First user: {json.dumps(data['Resources'][0], indent=2)}")
        else:
            print(f"Error: {response.text}")


async def test_delete_user(token: str, user_id: str) -> None:
    """Test deleting a user via SCIM."""
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{SCIM_BASE_URL}/Users/{user_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"Delete User Status: {response.status_code}")
        if response.status_code != 204:
            print(f"Error: {response.text}")


async def main():
    """Run all tests."""
    try:
        # Get authentication token
        token = await get_token()
        
        # Test service provider config
        await test_service_provider_config(token)
        
        # Test listing users
        await test_list_users(token)
        
        # Test creating a user
        user_data = await test_create_user(token)
        if not user_data:
            return
        
        user_id = user_data["id"]
        
        # Test getting a specific user
        await test_get_user(token, user_id)
        
        # Test updating a user
        await test_update_user(token, user_id)
        
        # Test patching a user
        await test_patch_user(token, user_id)
        
        # Test filtering users
        await test_filter_users(token)
        
        # Test deleting a user
        await test_delete_user(token, user_id)
        
        # Verify the user was deleted
        await test_get_user(token, user_id)
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())