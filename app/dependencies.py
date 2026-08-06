
from app.db import DatabaseConnect

database = DatabaseConnect()


def get_session():
    #Yields a session and closes it when the request finishes.
    session = database.session_local()
    try:
        yield session
    finally:
        session.close()
