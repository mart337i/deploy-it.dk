# Deploy-it.dk deployment API

## Install 
```sh
apt install -y postgresql python3-pip python3-dev python3-venv build-essential libxml2-dev libxslt1-dev libldap2-dev libsasl2-dev libssl-dev libffi-dev libjpeg-dev libpq-dev
```

```sh
python3 -m venv .venv
```

```sh
source .venv/bin/actiavte

```
```sh
curl -sSL https://install.python-poetry.org | python3 -
```

```sh
poetry install
```

```sh
pip install -e .

```

## Configure
run `clicx server --save` with the parametors you want to run the service with. like `--host`.

## Usage

- All .env files will be loaded if they are loacted in the addons folder
- All Commands will be loaded in the cli dir inside addons folder (app = typer.Typer(help="Test commands")) Use app as the varibale name, other wise it dosent work.
- All Routes will be loaded inside the addons folder (router = APIRouter()) use router, other wise it donsent work. 