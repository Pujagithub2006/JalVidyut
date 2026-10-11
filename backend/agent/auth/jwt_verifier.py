import hmac
import hashlib
import json
import base64
import time
from typing import Dict, Any
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()
AUTH_SIGNING_SECRET = "JALVIDYUT_COGNITO_STAGING_KEY_2026"

def create_simulated_cognito_token(username: str, role: str, zone: str, expires_in: int = 3600) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": f"user-{username}",
        "cognito:username": username,
        "custom:role": role,
        "custom:zone": zone,
        "iss": "https://cognito-idp.ap-south-1.amazonaws.com/ap-south-1_JalVidyutPool",
        "exp": int(time.time()) + expires_in,
        "iat": int(time.time())
    }
    encoded_header = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b'=').decode()
    encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b'=').decode()
    sig_base = f"{encoded_header}.{encoded_payload}"
    sig = hmac.new(AUTH_SIGNING_SECRET.encode(), sig_base.encode(), hashlib.sha256).digest()
    encoded_sig = base64.urlsafe_b64encode(sig).rstrip(b'=').decode()
    return f"{sig_base}.{encoded_sig}"

def verify_cognito_jwt(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    token = credentials.credentials
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="Invalid JWT structure")
        header_b64, payload_b64, sig_b64 = parts
        sig_base = f"{header_b64}.{payload_b64}"
        expected = hmac.new(AUTH_SIGNING_SECRET.encode(), sig_base.encode(), hashlib.sha256).digest()
        provided = base64.urlsafe_b64decode(sig_b64 + "=="[:len(sig_b64) % 4])
        if not hmac.compare_digest(expected, provided):
            raise HTTPException(status_code=401, detail="JWT signature verification failed")
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + "=="[:len(payload_b64) % 4])
        claims = json.loads(payload_bytes.decode())
        if claims.get("exp", 0) < time.time():
            raise HTTPException(status_code=401, detail="Token has expired")
        return claims
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=401, detail=f"Authentication rejected: {str(e)}")
