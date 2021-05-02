from fastapi import WebSocket

class User:
    def __init__(self, discord_id, username, avatar):
        self.discord_id:str = discord_id
        self.username:str = username
        self.avatar:str = avatar
        self.friends:list = []
        self.box_id: str = ""
