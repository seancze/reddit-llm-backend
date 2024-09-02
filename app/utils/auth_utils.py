import jwt
import os
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import PyJWTError
from dotenv import load_dotenv
from typing import Optional

load_dotenv()


auth_scheme = HTTPBearer()


def verify_token_or_anonymous(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
):
    if auth_credentials is None:
        return None
    try:
        return verify_token(auth_credentials)
    except HTTPException:
        return None


def verify_token(auth_credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    try:
        token = auth_credentials.credentials
        header = jwt.get_unverified_header(token)
        algorithm = header["alg"]
        payload = jwt.decode(
            auth_credentials.credentials,
            os.environ.get("JWT_SECRET"),
            algorithms=[algorithm],
        )
        return payload["username"]

    except PyJWTError as e:
        print(f"JWT Error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
