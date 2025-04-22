import datetime
import subprocess

def get_version():
    now = datetime.datetime.now()
    return f"{now.year}.{now.month}.{now.day}.{now.hour}{now.minute:02d}"

def get_api_version():
    try:
        commit_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode().strip()
        return f"{get_version()}-{commit_hash}"
    except:
        return get_version()