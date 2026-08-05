
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import Settings

class DatabaseConnect:
    def __init__(self, 
                 database_url: str=None):
        self.settings = Settings(database_url)

        self.engine = create_engine(self.settings.database_url, 
                                    connect_args={"check_same_thread": False}) 
        #TODO: some docs say used check_same_thread for multi-thread application, should check it later if face any issue
        self.session_local = sessionmaker(bind=self.engine, 
                                          expire_on_commit=False)

    def get_engine(self):
        return self.engine
    
    def __del__(self):
        # I know it is bad practice, but just want to some PoC, quick example
        # and I still have some guards for the engine and session_local to be closed properly, 
        # so I think it is fine for now
        try:
            self.engine.dispose()
        except Exception:
            pass
        
        try:
            self.session_local.close_all()
        except Exception:  
            pass

