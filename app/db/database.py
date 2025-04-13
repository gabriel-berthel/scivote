import aiomysql
import os

_pool = None

async def create_pool():
    global _pool
    if _pool is None:
        db_host = os.getenv("DB_HOST")
        db_user = os.getenv("MYSQL_USER")
        db_password = os.getenv("MYSQL_PASSWORD")
        db_name = os.getenv("MYSQL_DATABASE")
        
        if not db_host or not db_user or not db_password or not db_name:
            raise ValueError(
                "Missing one or more required environment variables: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME"
            )

        print(f"Connecting to DB at {db_host} with user {db_user} and db {db_name}")

        _pool = await aiomysql.create_pool(
            host=db_host,
            port=3306,
            user=db_user,
            password=db_password,
            db=db_name,
            autocommit=True
        )
        
    return _pool
