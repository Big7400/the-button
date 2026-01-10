
import os
from pydantic import BaseModel

class Settings(BaseModel):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_ME_NOW")  # set in .env or shell
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # Bootstrap admin behavior
    # Option A: if no admins exist, auto-promote the first registered user (safe for local dev)
    AUTO_PROMOTE_FIRST_ADMIN: bool = os.getenv("AUTO_PROMOTE_FIRST_ADMIN", "true").lower() == "true"

    # Option B: only auto-promote if email matches this value
    BOOTSTRAP_ADMIN_EMAIL: str | None = os.getenv("BOOTSTRAP_ADMIN_EMAIL")

settings = Settings()
