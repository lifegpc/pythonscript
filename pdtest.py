from base64 import b64decode, b64encode
from hashlib import sha512
from typing import Union
from cryptography.hazmat.primitives import serialization as ser
from cryptography.hazmat.primitives.asymmetric import padding
import requests as r
from urllib.parse import urlparse, urlencode
from posixpath import basename

HOST = "http://localhost:8080"
HEADERS = {}


def check_err(re):
    if re['ok']:
        return re['result']
    else:
        raise ValueError(re['code'], re['msg'], re['debug_msg'])


def post(path: str, token: Union[bytes, str] = None, token_id: int = None,
         data=None):
    if data is None:
        data = {}
    if token is None or token_id is None:
        return r.post(f"{HOST}/{path}", data=data, headers=HEADERS)
    if isinstance(token, str):
        token = b64decode(token)
    keys = sorted([i for i in data.keys()])
    u = sha512()
    u.update(token)
    for key in keys:
        u.update(key.encode() if isinstance(key, str) else key)
        v = data[key]
        u.update(v.encode() if isinstance(v, str) else v)
    h = {'X-TOKEN-ID': str(token_id), 'X-SIGN': u.hexdigest()}
    h.update(HEADERS)
    return r.post(f"{HOST}/{path}", headers=h, data=data)


def gen_sign(data, token: bytes):
    keys = sorted([i for i in data.keys()])
    u = sha512()
    u.update(token)
    for key in keys:
        u.update(key.encode() if isinstance(key, str) else key)
        v = data[key]
        u.update(v.encode() if isinstance(v, str) else v)
    return u.hexdigest()


def get(path: str, token: Union[bytes, str] = None, token_id: int = None,
        data=None):
    if data is None:
        data = {}
    if token is None or token_id is None:
        return r.get(f"{HOST}/{path}", data=data, headers=HEADERS)
    if isinstance(token, str):
        token = b64decode(token)
    h = {'X-TOKEN-ID': str(token_id), 'X-SIGN': gen_sign(data, token)}
    h.update(HEADERS)
    return r.get(f"{HOST}/{path}", headers=h, data=data)


def options(path: str):
    return r.options(f"{HOST}/{path}")


def add_user(username: str, password: str, name: str,
             token: Union[bytes, str] = None, token_id: int = None):
    re = post("/auth/status").json()
    re2 = check_err(post("/auth/pubkey").json())
    key = ser.load_pem_public_key(re2['key'].encode())
    if re['has_root_user']:
        if token is None or token_id is None:
            raise ValueError("Token is needed.")
    else:
        token = None
        token_id = None
    pas = key.encrypt(password.encode(), padding.PKCS1v15())
    return check_err(post("/auth/user/add", token, token_id, {"username": username, "name": name, "password": b64encode(pas)}).json())  # noqa: E501


def get_proxy_pixiv_url(url: str, secrets: str):
    u = urlparse(url)
    if u.scheme not in ['http', 'https']:
        raise ValueError("Invalid url.")
    if not u.netloc.endswith(".pximg.net"):
        raise ValueError("Server only accept pximg.net URL.")
    data = {'url': url}
    data['sign'] = gen_sign(data, secrets.encode())
    name = basename(u.path)
    return f"{HOST}/proxy/pixiv/{name}?{urlencode(data)}"
