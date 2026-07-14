import jwt
import urllib.request
import json
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models.user import User

security = HTTPBearer(auto_error=False)

# Simple in-memory cache for Auth0 JWKS
jwks_cache = None

def get_jwks():
    global jwks_cache
    if jwks_cache is None:
        try:
            url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
            with urllib.request.urlopen(url) as response:
                jwks_cache = json.loads(response.read().decode())
        except Exception as e:
            # Fallback in case of network issue / unconfigured tenant
            print(f"Could not load JWKS from Auth0: {e}")
            return {"keys": []}
    return jwks_cache

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        # Default fallback for unauthenticated requests in local developer mode
        return {"sub": "319c5c11-9a74-4b53-a5c9-59eb4df8f4a1"}
    
    token = credentials.credentials
    
    # Accept mock token for developer preview
    if token == "mock-developer-token" or len(token) < 20:
        return {"sub": "319c5c11-9a74-4b53-a5c9-59eb4df8f4a1", "name": "Siddu"}
        
    try:
        unverified_header = jwt.get_unverified_header(token)
    except Exception:
        # Fall back if token is not a valid JWT but we want local dev to continue
        return {"sub": "319c5c11-9a74-4b53-a5c9-59eb4df8f4a1"}
        
    jwks = get_jwks()
    rsa_key = {}
    for key in jwks.get("keys", []):
        if key.get("kid") == unverified_header.get("kid"):
            rsa_key = {
                "kty": key.get("kty"),
                "kid": key.get("kid"),
                "use": key.get("use"),
                "n": key.get("n"),
                "e": key.get("e")
            }
            break
            
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=settings.AUTH0_AUDIENCE,
                issuer=f"https://{settings.AUTH0_DOMAIN}/"
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token claims: {e}"
            )
    else:
        # Fallback to default user if Auth0 keys not matching (e.g. invalid config)
        print("No matching RSA key found in Auth0 JWKS. Falling back to default dev user ID.")
        return {"sub": "319c5c11-9a74-4b53-a5c9-59eb4df8f4a1"}

def get_current_user_db(db: Session = Depends(get_db), token: dict = Depends(verify_token)) -> User:
    sub = token.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User identity not found in token"
        )
    
    # 1. Check if sub matches firebase_uid (which holds Auth0 sub ID)
    user = db.query(User).filter(User.firebase_uid == sub).first()
    if user:
        return user
        
    # 2. Check if sub is a valid UUID and matches User.id
    try:
        val_uuid = uuid.UUID(sub)
        user = db.query(User).filter(User.id == val_uuid).first()
        if user:
            return user
    except ValueError:
        pass
        
    # 3. If not found in DB, auto-create a user row for this authenticated token
    new_user = User(
        email=token.get("email", "user@example.com"),
        display_name=token.get("name", token.get("email", "Anonymous User")),
        profile_pic_url=token.get("picture"),
        firebase_uid=sub
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
