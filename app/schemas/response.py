from pydantic import BaseModel
from typing import Optional, Any, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')


class StandardResponse(BaseModel, Generic[T]):
    """Standardized API response structure"""
    success: bool
    message: str
    status_code: int
    data: Optional[T] = None
    timestamp: datetime = datetime.utcnow()
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "status_code": 200,
                "data": {},
                "timestamp": "2024-01-01T00:00:00"
            }
        }


def success_response(
    message: str,
    data: Any = None,
    status_code: int = 200
) -> dict:
    """Create a success response"""
    return {
        "success": True,
        "message": message,
        "status_code": status_code,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }


def error_response(
    message: str,
    status_code: int = 400,
    data: Any = None
) -> dict:
    """Create an error response"""
    return {
        "success": False,
        "message": message,
        "status_code": status_code,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
