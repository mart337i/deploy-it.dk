import typer
from typing import Optional, Annotated
from clicx.database.sql import Curser
from clicx.database.models import Model
from clicx._models.users import User
import bcrypt

from sqlalchemy import text
import rich

cli = typer.Typer(name="database")

@cli.command(
    help="Create database tables and admin user",
)
def create(
    db_name: Annotated[str, typer.Argument(help="Database name")],
    username: Annotated[str, typer.Option(help="Admin username for the application")],
    password: Annotated[str, typer.Option(help="Admin password for the application", prompt=True, hide_input=True)],
):
    """Init database schema and admin user"""
    try:
        typer.echo(f"Initializing database '{db_name}'...")
        
        db = Curser(dbname=db_name)
        
        Model.metadata.create_all(bind=db.engine)
        
        typer.echo("Tables created.")
        
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        with db.cr() as session:  # Note the () here - we're calling the method
            existing = session.query(User).filter_by(username=username).first()
            if existing:
                typer.echo(f"Admin user '{username}' already exists.")
            else:
                admin = User(username=username, password=hashed_pw)
                session.add(admin)
                typer.echo(f"Admin user '{username}' created.")
    except Exception as e:
        typer.echo(f"Error during initialization: {str(e)}", err=True)
        raise typer.Exit(code=1)

@cli.command(
    help="Test connection",
)
def test_connection(
    db_name: Annotated[str, typer.Argument(help="Database name")],
):
    try:
        conn = Curser(dbname=db_name)
        with conn.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        rich.print("Connection test succeeded")
    except Exception as e:
        rich.print(f"Connection test failed: {e}")

@cli.command(
    help="Migrate tables",
)
def migrate(
    db_name: Annotated[str, typer.Argument(help="Database name")],
):
    raise NotImplementedError("Not implemented yet, but planned.")