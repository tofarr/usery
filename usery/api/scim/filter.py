from typing import Any, Dict, List, Optional, Tuple, Union
import re
from sqlalchemy import and_, or_, not_, Column, String, Boolean
from sqlalchemy.sql.expression import BinaryExpression, UnaryExpression

# SCIM filter operators
OPERATORS = {
    "eq": "==",
    "ne": "!=",
    "co": "contains",
    "sw": "startswith",
    "ew": "endswith",
    "gt": ">",
    "ge": ">=",
    "lt": "<",
    "le": "<=",
    "pr": "present"
}

# Mapping of SCIM attributes to User model attributes
ATTRIBUTE_MAP = {
    "id": "id",
    "userName": "username",
    "emails.value": "email",
    "displayName": "full_name",
    "name.formatted": "full_name",
    "active": "is_active",
    "externalId": None,  # Not directly mapped
    "photos.value": "avatar_url"
}


class FilterParser:
    """Parser for SCIM filter expressions."""
    
    def __init__(self, model):
        """Initialize with the SQLAlchemy model to query."""
        self.model = model
    
    def parse(self, filter_string: str) -> Any:
        """Parse a SCIM filter string and return a SQLAlchemy filter expression."""
        if not filter_string:
            return None
        
        # Handle logical operators
        if " and " in filter_string.lower():
            parts = self._split_logical(filter_string, " and ")
            return and_(*[self.parse(part) for part in parts])
        
        if " or " in filter_string.lower():
            parts = self._split_logical(filter_string, " or ")
            return or_(*[self.parse(part) for part in parts])
        
        if filter_string.lower().startswith("not "):
            return not_(self.parse(filter_string[4:]))
        
        # Handle parentheses
        if filter_string.startswith("(") and filter_string.endswith(")"):
            return self.parse(filter_string[1:-1])
        
        # Handle comparison expressions
        return self._parse_comparison(filter_string)
    
    def _split_logical(self, filter_string: str, operator: str) -> List[str]:
        """Split a filter string by logical operator, respecting parentheses."""
        result = []
        paren_count = 0
        current = ""
        
        i = 0
        while i < len(filter_string):
            # Check for operator
            if (paren_count == 0 and 
                filter_string[i:i+len(operator)].lower() == operator):
                result.append(current.strip())
                current = ""
                i += len(operator)
                continue
            
            # Track parentheses
            if filter_string[i] == "(":
                paren_count += 1
            elif filter_string[i] == ")":
                paren_count -= 1
            
            current += filter_string[i]
            i += 1
        
        if current:
            result.append(current.strip())
        
        return result
    
    def _parse_comparison(self, expr: str) -> Optional[BinaryExpression]:
        """Parse a comparison expression."""
        # Match the attribute, operator, and value
        # Format: attribute operator "value" or attribute operator value
        pattern = r'(\S+)\s+(eq|ne|co|sw|ew|gt|ge|lt|le|pr)\s+(?:"([^"]+)"|(\S+))'
        match = re.match(pattern, expr)
        
        if not match:
            return None
        
        attr_path, operator, quoted_value, unquoted_value = match.groups()
        value = quoted_value if quoted_value is not None else unquoted_value
        
        # Map SCIM attribute to model attribute
        model_attr = self._map_attribute(attr_path)
        if not model_attr:
            return None
        
        # Handle the 'pr' (present) operator
        if operator == "pr":
            return model_attr != None
        
        # Apply the operator
        if operator == "eq":
            return model_attr == value
        elif operator == "ne":
            return model_attr != value
        elif operator == "co":
            return model_attr.contains(value)
        elif operator == "sw":
            return model_attr.startswith(value)
        elif operator == "ew":
            return model_attr.endswith(value)
        elif operator == "gt":
            return model_attr > value
        elif operator == "ge":
            return model_attr >= value
        elif operator == "lt":
            return model_attr < value
        elif operator == "le":
            return model_attr <= value
        
        return None
    
    def _map_attribute(self, attr_path: str) -> Optional[Column]:
        """Map a SCIM attribute path to a model attribute."""
        if attr_path in ATTRIBUTE_MAP:
            model_attr_name = ATTRIBUTE_MAP[attr_path]
            if model_attr_name:
                return getattr(self.model, model_attr_name)
        
        # Handle complex attributes or custom extensions
        # This would need to be expanded for more complex attribute mapping
        
        return None