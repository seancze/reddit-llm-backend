import jwt
import os
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import PyJWTError
from dotenv import load_dotenv

load_dotenv()


auth_scheme = HTTPBearer()


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
