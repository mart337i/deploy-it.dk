import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
import psycopg2
from alembic.config import Config
from alembic import command
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """SQLAlchemy wrapper with transaction and migration support"""
    def __init__(
            self,
            username=None,
            password=None,
            hostname=None,
            database_name=None,
            driver_and_dialect="postgresql+psycopg2",
            migrations_dir="migrations"
        ) -> None:
        """Initialize with SQLAlchemy and Alembic migration support"""
        # Get credentials from environment variables if not provided
        self.username = username or os.environ.get('DBUsername')
        self.password = password or os.environ.get('DBPassword')
        self.hostname = hostname or os.environ.get('DBHostname')
        self.database_name = database_name or os.environ.get('DBName')
        self.driver_and_dialect = driver_and_dialect
        self.migrations_dir = migrations_dir
        
        # Construct connection string
        self._connection_string = f"{self.driver_and_dialect}://{self.username}:{self.password}@{self.hostname}/{self.database_name}"
        self.engine = create_engine(url=self._connection_string)
        
        self.declarative_base = declarative_base()
        self.Session = sessionmaker(bind=self.engine)
    
    def init_database(self):
        """Initialize the database if it doesn't exist and create tables"""
        logger.info(f"Initializing database: {self.database_name}")
        if not database_exists(self.engine.url):
            logger.info(f"Creating database: {self.database_name}")
            create_database(self.engine.url)
        else:
            logger.info(f"Database already exists: {self.database_name}")
        
        # Create all tables based on models
        logger.info("Creating database schema from models")
        self.declarative_base.metadata.create_all(self.engine)
        
        # Initialize Alembic if migrations directory exists
        if os.path.exists(self.migrations_dir):
            self._init_alembic()
        
        return True
    
    def update_database(self):
        """Update database schema using Alembic migrations"""
        logger.info("Updating database schema using migrations")
        if not database_exists(self.engine.url):
            raise psycopg2.DatabaseError("Database does not exist! Run init_database first")
        
        alembic_cfg = self._get_alembic_config()
        command.upgrade(alembic_cfg, "head")
        logger.info("Database schema updated successfully")
        return True
    
    def create_migration(self, message):
        """Create a new migration file"""
        logger.info(f"Creating new migration: {message}")
        alembic_cfg = self._get_alembic_config()
        command.revision(alembic_cfg, autogenerate=True, message=message)
        logger.info("Migration file created successfully")
        return True
    
    def _get_alembic_config(self):
        """Get Alembic configuration"""
        alembic_cfg = Config(os.path.join(self.migrations_dir, "alembic.ini"))
        alembic_cfg.set_main_option("script_location", self.migrations_dir)
        alembic_cfg.set_main_option("sqlalchemy.url", self._connection_string)
        return alembic_cfg
    
    def _init_alembic(self):
        """Initialize Alembic if not already initialized"""
        if not os.path.exists(os.path.join(self.migrations_dir, "alembic.ini")):
            logger.info("Initializing Alembic migration environment")
            alembic_cfg = Config()
            alembic_cfg.set_main_option("script_location", self.migrations_dir)
            alembic_cfg.set_main_option("sqlalchemy.url", self._connection_string)
            command.init(alembic_cfg, self.migrations_dir)
            logger.info("Alembic migration environment initialized")
    
    def execute(self, query, params=None):
        """Execute a raw SQL query with optional parameters"""
        with self.engine.connect() as connection:
            if params:
                return connection.execute(query, params)
            else:
                return connection.execute(query)
    
    def validate_database(self):
        """Validate that the database exists"""
        if not database_exists(self.engine.url):
            raise psycopg2.DatabaseError("Database does not exist! Run init_database first")
        return True
    
    def get_session(self):
        """Get a new session"""
        return self.Session()


# Usage example:
# db = DatabaseManager(username="postgres", password="password", hostname="localhost", database_name="mydb")
# db.init_database()  # Initialize database and tables
# db.create_migration("add users table")  # Create a new migration
# db.update_database()  # Apply all migrations