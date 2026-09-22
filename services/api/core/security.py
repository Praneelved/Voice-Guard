from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.database import async_session_maker
from models.domain import Organization, User

security = HTTPBearer(auto_error=False)

# This needs to be set in the environment or passed via config
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "placeholder-secret")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    token = credentials.credentials
    try:
        # Supabase uses HS256 by default.
        # Ensure we disable audience verification if it's not strictly "authenticated"
        payload = jwt.decode(
            token, 
            JWT_SECRET, 
            algorithms=["HS256"], 
            options={"verify_aud": False}
        )
        
        # In Supabase JWTs, the 'sub' claim is the user's UUID.
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: missing sub"
            )
            
        # Ensure user's personal organization and user exist
        async with async_session_maker() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                import uuid
                uid = uuid.UUID(user_id)
                # Check org first just in case
                stmt_org = select(Organization).where(Organization.id == user_id)
                res_org = await session.execute(stmt_org)
                org = res_org.scalar_one_or_none()
                
                if not org:
                    org = Organization(id=uid, name=f"Personal Org - {payload.get('email', 'User')}")
                    session.add(org)
                    
                user = User(id=uid, org_id=uid, email=payload.get("email") or f"{user_id}@example.com", role=payload.get("role") or "authenticated")
                session.add(user)
                await session.commit()

        return {
            "id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role")
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
