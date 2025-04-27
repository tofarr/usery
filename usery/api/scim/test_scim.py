"""
Simple test script to verify SCIM implementation.
This doesn't require running the full server.
"""

import asyncio
import uuid
from typing import Dict, Any

from usery.api.scim.schemas import ScimUser, ScimName, ScimEmail
from usery.api.scim.converters import scim_to_user_create, scim_to_user_update
from usery.api.scim.filter import FilterParser
from usery.models.user import User as UserModel


def test_scim_to_user_create():
    """Test converting SCIM user to UserCreate."""
    # Create a SCIM user
    scim_user = ScimUser(
        id=str(uuid.uuid4()),
        userName="testuser",
        name=ScimName(formatted="Test User"),
        emails=[ScimEmail(value="test@example.com", primary=True)],
        active=True,
        meta={
            "resourceType": "User",
            "created": "2023-01-01T00:00:00Z",
            "lastModified": "2023-01-01T00:00:00Z",
            "location": "https://example.com/scim/v2/Users/123"
        }
    )
    
    # Convert to UserCreate
    user_create = scim_to_user_create(scim_user)
    
    # Verify conversion
    assert user_create.email == "test@example.com"
    assert user_create.username == "testuser"
    assert user_create.full_name == "Test User"
    assert user_create.is_active is True
    
    print("SCIM to UserCreate conversion test passed!")


def test_filter_parser():
    """Test SCIM filter parser."""
    # Create a filter parser
    parser = FilterParser(UserModel)
    
    # Test simple filter
    filter_expr = parser.parse('userName eq "john"')
    assert filter_expr is not None
    
    # Test complex filter
    filter_expr = parser.parse('userName eq "john" and active eq true')
    assert filter_expr is not None
    
    # Test filter with parentheses
    filter_expr = parser.parse('(userName eq "john") or (userName eq "jane")')
    assert filter_expr is not None
    
    print("Filter parser test passed!")


def main():
    """Run all tests."""
    test_scim_to_user_create()
    test_filter_parser()
    print("All tests passed!")


if __name__ == "__main__":
    main()