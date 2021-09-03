import requests, json, os, urllib
from server.user import User
import server.db as db
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()


API_ENDPOINT = "https://discord.com/api/v8"
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI")
DISCORD_AUTH_URL = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={urlparse(REDIRECT_URI).geturl()}&response_type=code&scope=identify"


def exchange_code(code: str) -> dict:
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(f"{API_ENDPOINT}/oauth2/token", data=data, headers=headers)
    r.raise_for_status()
    return r.json()


def get_user_creds(access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(f"{API_ENDPOINT}/users/@me", headers=headers)
    return r.json()


def server_join(user_id: str, access_token: str):
    data = json.dumps({"access_token": access_token})
    headers = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}
    r = requests.put(
        f"{API_ENDPOINT}/guilds/838214461428596786/members/{user_id}",
        data=data,
        headers=headers,
    )


def authorize_user(auth_code: str) -> User:
    exchange = exchange_code(auth_code)
    access_token = exchange.get("access_token")
    user_creds = get_user_creds(access_token)
    username = user_creds["username"] + "#" + user_creds["discriminator"]
    avatar = f"https://cdn.discordapp.com/avatars/{user_creds['id']}/{user_creds['avatar']}.png"
    user = db.create_new_user(user_creds["id"], username, avatar)
    # server_join(user.discord_id, access_token)

    return user


def ping_user(user_id: str):
    requests.post()
