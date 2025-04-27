from enum import Enum
from typing import Generic, List, TypeVar, Optional, Any, Dict
from pydantic import BaseModel, Field, conlist

# Define a generic type variable for the item types
T = TypeVar('T')


class BatchOperationType(str, Enum):
    """Enum for batch operation types."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class BatchOperation(BaseModel, Generic[T]):
    """Schema for a single batch operation."""
    
    operation: BatchOperationType
    id: Optional[Any] = None  # ID for update/delete operations
    data: Optional[T] = None  # Data for create/update operations


class BatchRequest(BaseModel, Generic[T]):
    """Schema for batch request."""
    
    operations: conlist(BatchOperation[T], max_length=100) = Field(
        ..., 
        description="List of operations to perform (max 100)"
    )


class BatchResponseItem(BaseModel):
    """Schema for a single batch response item."""
    
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    index: int = Field(..., description="Index of the operation in the request")


class BatchResponse(BaseModel):
    """Schema for batch response."""
    
    results: List[BatchResponseItem]
    success_count: int
    error_count: int