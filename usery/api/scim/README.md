# SCIM API Implementation

This directory contains the implementation of the System for Cross-domain Identity Management (SCIM) v2.0 API for user administration.

## Overview

SCIM is a standardized API for managing user identities. This implementation provides the following endpoints:

### User Resource Endpoints

- `GET /scim/v2/Users` - List/search users
- `GET /scim/v2/Users/{id}` - Get a specific user
- `POST /scim/v2/Users` - Create a user
- `PUT /scim/v2/Users/{id}` - Replace a user
- `PATCH /scim/v2/Users/{id}` - Update a user
- `DELETE /scim/v2/Users/{id}` - Delete a user

### Service Provider Configuration Endpoint

- `GET /scim/v2/ServiceProviderConfig` - Get service provider configuration

## Features

### Filtering

The implementation supports SCIM filtering syntax for querying users. For example:

```
GET /scim/v2/Users?filter=userName eq "john"
GET /scim/v2/Users?filter=emails.value co "example.com"
GET /scim/v2/Users?filter=name.formatted sw "John"
```

Supported filter operators:
- `eq` - Equal
- `ne` - Not equal
- `co` - Contains
- `sw` - Starts with
- `ew` - Ends with
- `gt` - Greater than
- `ge` - Greater than or equal
- `lt` - Less than
- `le` - Less than or equal
- `pr` - Present (has value)

Logical operators:
- `and` - Logical AND
- `or` - Logical OR
- `not` - Logical NOT

### Pagination

The implementation supports pagination with the following parameters:

- `startIndex` - The 1-based index of the first result (default: 1)
- `count` - The maximum number of results to return (default: 100)

Example:
```
GET /scim/v2/Users?startIndex=1&count=10
```

### Sorting

The implementation supports sorting with the following parameters:

- `sortBy` - The attribute to sort by
- `sortOrder` - The sort order (`ascending` or `descending`)

Example:
```
GET /scim/v2/Users?sortBy=userName&sortOrder=ascending
```

## Schema Mapping

The implementation maps between the SCIM User schema and the internal User model as follows:

| SCIM Attribute | Internal Attribute |
|----------------|-------------------|
| id | id |
| userName | username |
| name.formatted | full_name |
| emails[primary].value | email |
| active | is_active |
| photos[primary].value | avatar_url |

## Authentication

All SCIM endpoints require authentication with a valid access token. The token should be provided in the `Authorization` header as a Bearer token:

```
Authorization: Bearer <token>
```

## Error Handling

The implementation returns standard SCIM error responses with appropriate HTTP status codes:

- `400 Bad Request` - Invalid request syntax
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource already exists
- `500 Internal Server Error` - Server error

## Testing

A test script is provided in `/workspace/usery/tests/test_scim.py` to verify the SCIM implementation.

## References

- [SCIM 2.0 RFC](https://tools.ietf.org/html/rfc7644)
- [SCIM 2.0 Schema](https://tools.ietf.org/html/rfc7643)