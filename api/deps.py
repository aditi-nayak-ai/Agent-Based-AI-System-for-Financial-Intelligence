from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.auth import verify_token

# HTTPBearer makes the /docs Authorize box ask for one thing: the token.
# (OAuth2PasswordBearer asked for a username and password and posted them as a
# form to /login, but /login takes JSON, so Authorize failed with a 422.)
bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)):
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return verify_token(creds.credentials)
