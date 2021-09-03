from server.user import User
from typing import Optional
from fastapi import Request
import pickle

db = {"users": {}}


def dump():
    global db
    with open("db.p", "wb") as db_file:
        pickle.dump(db, db_file)


def load():
    global db
    try:
        with open("db.p", "rb") as db_file:
            db = pickle.load(db_file)
    except Exception as e:
        print(e)
        return


def create_new_user(discord_id: str, username: str, avatar: str) -> User:
    user = find_user_by_id(discord_id)
    if user is None:
        user = User(discord_id, username, avatar)

    db["users"][discord_id] = user
    return user


def find_user_by_request(request: Request) -> Optional[User]:
    return find_user_by_id(request.cookies.get("session", None))


def find_user_by_id(id: str) -> Optional[User]:
    return db["users"].get(id, None)


def find_user_by_username(username: str) -> Optional[User]:
    for user in db["users"].values():
        if user.username == username:
            return user
    return None


def find_user_by_box_id(box_id: str) -> Optional[User]:
    for user in db["users"].values():
        if user.box_id == box_id:
            return user
    return None


def find_user_info(id: str) -> dict:
    user = find_user_by_id(discord_id)
    if user is None:
        return {}

    return {
        "id": user.id,
        "username": user.username,
        "friends": [{"id": f.id, "username": f.username} for f in user.friends],
    }
