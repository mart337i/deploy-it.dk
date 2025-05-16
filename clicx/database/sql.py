from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from typing import Generator, Any
from contextlib import contextmanager

class connection():
    def __init__(self, dbname: str, user: str = '$USER') -> None:
        self.dbname = dbname
        self.user = user
        self.engine = self.get_engine()

    def get_engine(self):
            # NOTE: Connection via Unix socket
            # TODO Rewrite to support TCP
            url = f'postgresql+psycopg2://{self.user}@/{self.dbname}'
            return create_engine(url)


class Curser(connection):
    def __init__(self, dbname: str, user: str = '$USER') -> None:
        super().__init__(dbname, user)
        self.curser: Generator[Session, Any, None] = self.cr()

    @contextmanager
    def cr(self) -> Generator[Session]:
        session = Session(self.engine)
        try: 
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()