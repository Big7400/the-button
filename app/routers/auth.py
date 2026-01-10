from fastapi import APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return {
        "access_token": "TEST_TOKEN",
        "token_type": "bearer"
    }
