import os
from pathlib import Path
DEV_SECRET_KEY = "dev-only-insecure-secret-change-me-in-production"


class Settings:
    def __init__(self, database_url: str=None):
        # getting database url from environment variable or defaulting to sqlite database in the project root directory
        BASE_DIR = Path(__file__).resolve().parent.parent
        self.database_url: str = \
            database_url or \
                os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'bookmarks.db'}")

        self.jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", DEV_SECRET_KEY)
        self.jwt_algorithm: str = "HS256"
        self.jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

if __name__ == "__main__":
    settings = Settings()
    print(settings.database_url)
    print("using dev secret:", settings.jwt_secret_key == DEV_SECRET_KEY)