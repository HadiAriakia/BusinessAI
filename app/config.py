import os
from pathlib import Path



class Settings:
    def __init__(self, database_url: str=None):
        # getting database url from environment variable or defaulting to sqlite database in the project root directory
        # Getting the database URL from the environment variable is good for production, but I just add this feature now 
        # just in case I need to use with Docker later
        BASE_DIR = Path(__file__).resolve().parent.parent
        self.database_url: str = \
            database_url or \
                os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'bookmarks.db'}")

if __name__ == "__main__":
    settings = Settings()
    print(settings.database_url)