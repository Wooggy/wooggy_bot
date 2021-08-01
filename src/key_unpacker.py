import os
from dotenv import load_dotenv


def get_from_env(key: str) -> str:

    """Get KEY from .env file"""

    dotenv_path = os.path.join(os.path.abspath('../'), '.env')
    load_dotenv(dotenv_path)
    return os.environ.get(key)
