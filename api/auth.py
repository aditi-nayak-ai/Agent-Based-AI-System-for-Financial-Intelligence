import os
import secrets
import logging
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# No built in default. If SECRET_KEY is missing, a random key is made for this
# process only, so nobody can sign tokens with a key that is public in the repo.
# Set SECRET_KEY in production, otherwise every restart logs everyone out.
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_urlsafe(48)
    logger.warning("SECRET_KEY is not set. Using a random key for this process. Set SECRET_KEY in the environment.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        # require_exp: a token without an expiry time is rejected
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM], options={"require_exp": True}
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
