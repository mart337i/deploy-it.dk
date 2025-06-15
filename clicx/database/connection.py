from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session, sessionmaker
from typing import Generator, Any, Dict
from contextlib import contextmanager
import threading

class DatabaseConnection:
    _instances: Dict[str, 'DatabaseConnection'] = {}
    _lock = threading.Lock()
    
    def __new__(cls, dbname: str, user: str = 'egeskov'):
        key = f"{dbname}_{user}"
        if key not in cls._instances:
            with cls._lock:
                if key not in cls._instances:
                    cls._instances[key] = super().__new__(cls)
        return cls._instances[key]
    
    def __init__(self, dbname: str, user: str = 'egeskov') -> None:
        if hasattr(self, '_initialized'):
            return
        self.dbname = dbname
        self.user = user
        self.engine = self._get_engine()
        self.metadata = MetaData()
        self.SessionLocal = sessionmaker(bind=self.engine)
        self._initialized = True
    
    def _get_engine(self):
        # NOTE: Connection via Unix socket
        # TODO: Rewrite to support TCP
        url = f'postgresql+psycopg2://{self.user}@/{self.dbname}'
        return create_engine(url, echo=False)
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()