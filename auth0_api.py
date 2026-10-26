import os
import requests

def get_management_token():
    domain = os.getenv("AUTH0_DOMAIN")
    payload = {
        "client_id": os.getenv("AUTH0_CLIENT_ID"),
        "client_secret": os.getenv("AUTH0_CLIENT_SECRET"),
        "audience": f"https://{domain}/api/v2/",
        "grant_type": "client_credentials"
    }
    res = requests.post(f"https://{domain}/oauth/token", json=payload)
    res.raise_for_status()
    return res.json().get("access_token")