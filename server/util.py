from fastapi import Response, Request
from fastapi.responses import RedirectResponse
import base64

def redirect(url: str = "/", code: int = 303, msg_type: str = None, msg: str = None) -> Response:
    res = RedirectResponse(url=url, status_code=code)
    if msg_type and msg:
        res.set_cookie("msg_type", msg_type)
        res.set_cookie("msg", msg)
    return res

def redirect_msg(msg_type: str, msg: str) -> Response:
    return redirect(url="/", msg_type=msg_type, msg=msg)

def get_msg(request: Request, response: Response) -> (str, str):
    msg_type = request.cookies.get("msg_type", "")
    msg = request.cookies.get("msg", "")
    return msg_type, msg
