from fastapi import HTTPException, status
from app.models import Role

def require_role(user, role_name: str):
    if user.role is None or user.role.name != role_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User must have role: {role_name}"
        )
    return True
