import rich
import typer
from clicx.utils import jinja

app = typer.Typer(help="Test commands")

@app.command()
def test_commands():
    pass

