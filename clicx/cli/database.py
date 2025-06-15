import typer
from typing import Optional, Annotated
from clicx.database.connection import DatabaseConnection
from clicx.database.base import Base
from clicx.database.registry import ModelRegistry
from sqlalchemy import text
import rich

cli = typer.Typer(name="database")

@cli.command(
    help="Create database tables and admin user",
)
def create(
    db_name: Annotated[str, typer.Argument(help="Database name")],
):
    """Init database schema and admin user"""
    try:
        typer.echo(f"Initializing database '{db_name}'...")
        
        # Import all models to ensure they're registered
        # This forces the model registration to happen
        try:
            from clicx.database import models  # Import your predefined models
            from clicx import _models  # Import your custom models
        except ImportError as e:
            typer.echo(f"Warning: Some models couldn't be imported: {e}")
        
        # Ensure all relationships are resolved
        ModelRegistry.resolve_relationships()
        
        # Create database connection
        db = DatabaseConnection(dbname=db_name)
        
        # Use Base.metadata instead of DatabaseConnection.metadata
        Base.metadata.create_all(bind=db.engine)
        
        typer.echo("Tables created successfully.")
        
        # Show created tables
        with db.get_session() as session:
            result = session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                typer.echo(f"Created {len(tables)} tables:")
                for table in tables:
                    typer.echo(f"  - {table}")
            else:
                typer.echo("No tables were created.")
        
        # Show registered models
        models = ModelRegistry.all_models()
        if models:
            typer.echo(f"\nRegistered {len(models)} models:")
            for model_name, model_class in models.items():
                table_name = getattr(model_class, '__tablename__', 'N/A')
                typer.echo(f"  - {model_name} -> {table_name}")
        
        # Uncomment and modify this section when you're ready to create admin user
        # from clicx._models.users import User
        # import bcrypt
        # 
        # username = "admin"
        # password = typer.prompt("Enter admin password", hide_input=True)
        # 
        # hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        # with db.get_session() as session:
        #     existing = session.query(User).filter_by(username=username).first()
        #     if existing:
        #         typer.echo(f"Admin user '{username}' already exists.")
        #     else:
        #         admin = User(username=username, password=hashed_pw)
        #         session.add(admin)
        #         typer.echo(f"Admin user '{username}' created.")
        
    except Exception as e:
        typer.echo(f"Error during initialization: {str(e)}", err=True)
        import traceback
        typer.echo(f"Full traceback:\n{traceback.format_exc()}", err=True)
        raise typer.Exit(code=1)

@cli.command(
    help="Drop all database tables",
)
def drop(
    db_name: Annotated[str, typer.Argument(help="Database name")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
):
    """Drop all database tables"""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to drop all tables in '{db_name}'?")
        if not confirm:
            typer.echo("Aborted.")
            raise typer.Exit()
    
    try:
        typer.echo(f"Dropping tables in database '{db_name}'...")
        
        # Import models to register them
        try:
            from clicx.database import models
            from clicx import _models
        except ImportError as e:
            typer.echo(f"Warning: Some models couldn't be imported: {e}")
        
        db = DatabaseConnection(dbname=db_name)
        Base.metadata.drop_all(bind=db.engine)
        
        typer.echo("All tables dropped successfully.")
        
    except Exception as e:
        typer.echo(f"Error dropping tables: {str(e)}", err=True)
        raise typer.Exit(code=1)

@cli.command(
    help="Show database schema information",
)
def info(
    db_name: Annotated[str, typer.Argument(help="Database name")],
):
    """Show database schema and model information"""
    try:
        typer.echo(f"Database info for '{db_name}':")
        
        # Import models
        try:
            from clicx.database import models
            from clicx import _models
        except ImportError as e:
            typer.echo(f"Warning: Some models couldn't be imported: {e}")
        
        db = DatabaseConnection(dbname=db_name)
        
        # Show registered models
        models = ModelRegistry.all_models()
        typer.echo(f"\n=== Registered Models ({len(models)}) ===")
        for model_name, model_class in models.items():
            table_name = getattr(model_class, '__tablename__', 'N/A')
            typer.echo(f"  {model_name} -> {table_name}")
            
            # Show fields if available
            if hasattr(model_class, '_fields'):
                for field_name, field_obj in model_class._fields.items():
                    field_type = type(field_obj).__name__
                    typer.echo(f"    - {field_name}: {field_type}")
        
        # Show actual database tables
        with db.get_session() as session:
            result = session.execute(text("""
                SELECT table_name, 
                       (SELECT COUNT(*) 
                        FROM information_schema.columns 
                        WHERE table_name = t.table_name 
                        AND table_schema = 'public') as column_count
                FROM information_schema.tables t
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """))
            tables = result.fetchall()
            
            typer.echo(f"\n=== Database Tables ({len(tables)}) ===")
            for table_name, column_count in tables:
                typer.echo(f"  {table_name} ({column_count} columns)")
        
    except Exception as e:
        typer.echo(f"Error getting database info: {str(e)}", err=True)
        raise typer.Exit(code=1)