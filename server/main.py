from typing import Optional

from fastapi import (
    FastAPI,
    Request,
    Response,
    Cookie,
    WebSocket,
    Form,
    WebSocketDisconnect,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

import requests
import os

from server.oauth import authorize_user, DISCORD_AUTH_URL
from server.user import User

from server.util import redirect, get_msg, redirect_msg
from dotenv import load_dotenv

import json, random

import server.db as db

app = FastAPI()

app.mount("/static", StaticFiles(directory="./server/static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup_event():
    db.load()


@app.on_event("shutdown")
def shutdown_event():
    db.dump()


def get_color():
    return 360 * random.random(), 70 + 70 * random.random(), 40 + 10 * random.random()


def get_colors():
    h, s, l = (
        360 * random.random(),
        25 + 70 * random.random(),
        85 + 10 * random.random(),
    )
    return f"hsl({h},{s}%,{l}%)", f"hsl({h},{s+80}%,{l-80}%)"


@app.get("/auth")
def auth_user(request: Request, code: Optional[str] = None):
    if code is not None:
        try:
            user = authorize_user(code)
        except Exception as e:
            return redirect(
                "/",
                msg_type="error",
                msg="There was an error authenticating with discord",
            )

        db.dump()

        response = redirect()
        response.set_cookie(
            key="session", value=user.discord_id, max_age=31622400, expires=31622400
        )
        return response
    else:
        return redirect(
            "/", msg_type="error", msg="There was an error authenticating with discord"
        )


@app.get("/")
def read_root(request: Request, response: Response):
    msg_type, msg = get_msg(request, response)

    user = db.find_user_by_request(request)

    fg, bg = get_colors()
    res = templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": user,
            "msg_type": msg_type,
            "msg": msg,
            "DISCORD_AUTH_URL": DISCORD_AUTH_URL,
            "fg": fg,
            "bg": bg,
        },
    )

    res.set_cookie("msg_type", "")
    res.set_cookie("msg", "")

    return res


@app.get("/box")
def box(request: Request, response: Response):
    fg, bg = get_colors()

    c = lambda hsl: f"hsla({hsl[0]}, {hsl[1]}%, {hsl[2]}%, 0.2)"
    return templates.TemplateResponse(
        "box.html",
        {
            "request": request,
            "fg": fg,
            "bg": bg,
            "box_colors": [c(get_color()) for _ in range(6)],
        },
    )


class BoxConnectionManager:
    def __init__(self):
        self.box_connections: dict[str, WebSocket] = {}

    async def add(self, box_id: str, websocket: WebSocket):
        await websocket.accept()
        self.box_connections[box_id] = websocket

    def delete(self, box_id: str):
        del self.box_connections[box_id]

    def has(self, box_id: str) -> bool:
        return box_id in self.box_connections

    async def send_json(self, box_id: str, message):
        await self.box_connections[box_id].send_json(message)


manager = BoxConnectionManager()


@app.websocket("/box/{box_id}")
async def box_websocket(websocket: WebSocket, box_id: str):
    try:
        await manager.add(box_id, websocket)

        box_user = db.find_user_by_box_id(box_id)
        if box_user:
            await update_user_box_friends(box_user)

        while True:
            data = await websocket.receive_json()
            if data.get("method", "") == "ping":
                to_user = db.find_user_by_username(data.get("to_username", ""))
                from_user = db.find_user_by_box_id(box_id)
                if from_user and to_user:
                    await ping(from_user.discord_id, to_user.discord_id)
    except WebSocketDisconnect:
        manager.delete(box_id)


@app.post("/connect")
async def connect_endpoint(request: Request, box_id: str = Form("")):
    if not manager.has(box_id) and box_id != "":
        return redirect_msg("error", "Invalid box code")

    user = db.find_user_by_request(request)
    if user is None:
        return redirect_msg("error", "You are not logged in")

    box_user = db.find_user_by_box_id(box_id)
    if box_user:
        if box_user == user:
            return redirect_msg("error", "You are already connected to this box")
        else:
            return redirect_msg("error", "This box is connected to someone else")

    user.box_id = box_id

    await update_user_box_friends(user)

    db.dump()

    return redirect()


async def update_user_box_friends(user: User):
    if user.box_id and manager.has(user.box_id):
        await manager.send_json(
            user.box_id,
            {"method": "friends", "friends": [f.username for f in user.friends]},
        )


async def ping(from_id: str, to_id: str) -> bool:
    from_user = db.find_user_by_id(from_id)
    to_user = db.find_user_by_id(to_id)
    if from_user is None or to_user is None:
        return False

    if to_user.box_id and manager.has(to_user.box_id):
        await manager.send_json(
            to_user.box_id, {"method": "ping", "from_username": from_user.username}
        )
        return True

    return False


@app.post("/ping_friend/{to_id}")
async def ping_endpoint(request: Request, to_id: str):
    successful = await ping(request.cookies.get("session", ""), to_id)

    if successful:
        return redirect_msg("msg", "Ping successfully sent!")
    else:
        return redirect_msg("error", "Ping not sent")


@app.post("/add_friend")
def add_friend(request: Request, friend_username: Optional[str] = Form(None)):
    user = db.find_user_by_request(request)
    if user is None:
        return redirect_msg("error", "You are not logged in")

    friend_user = db.find_user_by_username(friend_username)
    if friend_user is None:
        return redirect_msg("error", "User not found")

    if friend_user not in user.friends:
        user.friends.append(friend_user)
        update_user_box_friends(user)
    if user not in friend_user.friends:
        friend_user.friends.append(user)
        update_user_box_friends(friend_user)

    db.dump()

    return redirect()


@app.post("/remove_friend/{friend_id}")
def remove_friend(request: Request, friend_id: str):
    user = db.find_user_by_request(request)
    if user is None:
        return redirect_msg("error", "You are not logged in")

    friend_user = db.find_user_by_id(friend_id)
    if friend_user is None:
        return redirect_msg("error", "Friend does not exist")

    user.friends = [f for f in user.friends if f.discord_id != friend_id]
    friend_user.friends = [
        f for f in friend_user.friends if f.discord_id != user.discord_id
    ]

    update_user_box_friends(user)

    db.dump()

    return redirect()
