from passlib.hash import bcrypt
from fastapi import HTTPException
from db.database import create_pool
from itsdangerous import URLSafeSerializer, BadSignature
from fastapi import Request

SECRET_KEY = "mysecretkey"
serializer = URLSafeSerializer(SECRET_KEY)

class AuthService:
    def __init__(self, secret_key: str = SECRET_KEY):
        self.serializer = URLSafeSerializer(secret_key)

    async def register_user(self, email: str, password: str):
        hashed_password = bcrypt.hash(password)
        pool = await create_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    INSERT INTO users (email, hashed_password, is_verified)
                    VALUES (%s, %s, %s)
                """, (email, hashed_password, True))

    async def authenticate_user(self, email: str, password: str):
        pool = await create_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT id, hashed_password, is_verified FROM users WHERE email = %s
                """, (email,))
                result = await cur.fetchone()

                if not result:
                    raise HTTPException(status_code=401, detail="Invalid credentials")

                user_id, hashed_password, is_verified = result

                if not bcrypt.verify(password, hashed_password):
                    raise HTTPException(status_code=401, detail="Invalid credentials")

                if not is_verified:
                    raise HTTPException(status_code=403, detail="Email not verified")

                return user_id

    def is_authenticated(self, request: Request):
        signed_user_id = request.cookies.get("user_id")
        if not signed_user_id:
            raise HTTPException(status_code=401, detail="Not authenticated")
        try:
            user_id = self.serializer.loads(signed_user_id)
        except BadSignature:
            raise HTTPException(status_code=401, detail="Invalid cookie signature")
        return user_id

    def get_user_id(self, request: Request):
        signed_user_id = request.cookies.get("user_id")
        user_id = self.serializer.loads(signed_user_id)
        return user_id