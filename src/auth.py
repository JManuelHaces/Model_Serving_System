from fastapi import Header, HTTPException

from src.utils.config import get_config_value

# Getting the API Key from the file 'config.ini'
API_KEY = get_config_value('fastapi', 'api_key')

def authenticate(api_key: str = Header(...)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail='Invalid API Key')
