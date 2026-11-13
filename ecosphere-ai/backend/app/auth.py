"""Supabase Auth JWT validation; development bypass is opt-in and loopback-only."""
from dataclasses import dataclass
from urllib.parse import urlparse
import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import User

@dataclass
class Identity:
    subject: str
    email: str
    dev: bool = False

_jwks = None

def identity(request: Request) -> Identity:
    if settings.dev_auth_mode:
        if request.client is None or request.client.host not in ('127.0.0.1', '::1', 'localhost', 'testclient'):
            raise HTTPException(403, 'Development auth is restricted to loopback clients')
        return Identity('local-developer', 'developer@localhost', True)
    raw = request.headers.get('authorization', '')
    if not raw.startswith('Bearer '):
        raise HTTPException(401, 'Sign in through Supabase Auth to access real audits')
    if not settings.supabase_url:
        raise HTTPException(503, 'Supabase Auth is not configured')
    global _jwks
    try:
        issuer = settings.supabase_url.rstrip('/') + '/auth/v1'
        parsed = urlparse(settings.supabase_url)
        if parsed.scheme != 'https':
            raise ValueError('SUPABASE_URL must use HTTPS')
        if _jwks is None:
            _jwks = PyJWKClient(issuer + '/.well-known/jwks.json', cache_keys=True, lifespan=3600)
        token = raw[7:]
        key = _jwks.get_signing_key_from_jwt(token).key
        claims = jwt.decode(token, key, algorithms=['RS256', 'ES256'], audience=settings.supabase_jwt_audience, issuer=issuer, options={'require':['exp','iat','sub','aud','iss']})
        if claims.get('role') != 'authenticated':
            raise ValueError('Expected authenticated role')
        return Identity(str(claims['sub']), str(claims.get('email') or ''))
    except Exception as exc:
        raise HTTPException(401, 'Invalid or expired authentication token') from exc

def current_user(who: Identity = Depends(identity), db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.auth_sub == who.subject).first()
    if user is None:
        user = User(auth_sub=who.subject, email=who.email, role='auditor')
        db.add(user)
        db.commit()
        db.refresh(user)
    elif who.email and user.email != who.email:
        user.email = who.email
        db.commit()
    return user

def campus_user(user: User = Depends(current_user)) -> User:
    if not user.campus_id:
        raise HTTPException(409, 'Create your campus workspace before adding audit records')
    return user

def permit(user: User, *roles: str):
    if user.role not in roles:
        raise HTTPException(403, 'You do not have permission for this action')
