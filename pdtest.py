from base64 import b64decode, b64encode

from hashlib import sha512
from typing import Union
from cryptography.hazmat.primitives import serialization as ser
from cryptography.hazmat.primitives.asymmetric import padding
import requests as r
from urllib.parse import urlparse, urlencode
from posixpath import basename
from json import dumps as _dumps
from time import time

HOST = "http://localhost:8080"
HEADERS = {}


def dumps(obj):
    return _dumps(obj, ensure_ascii=False, separators=(',', ':'))


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
    if isinstance(data, dict):
        data['t'] = f"{round(time())}"
    h = {'X-TOKEN-ID': str(token_id), 'X-SIGN': gen_sign(data, token)}
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
    if isinstance(data, dict):
        data['t'] = f"{round(time())}"
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
    return check_err(post("auth/user/add", token, token_id, {"username": username, "name": name, "password": b64encode(pas)}).json())  # noqa: E501


def add_token(username: str, password: str):
    re = check_err(post("/auth/pubkey").json())
    key = ser.load_pem_public_key(re['key'].encode())
    pas = key.encrypt(password.encode(), padding.PKCS1v15())
    return check_err(post("/auth/token/add", None, None, {"username": username, "password": b64encode(pas)}).json())  # noqa: E501


def extend_token(token: Union[bytes, str], token_id: int):
    return check_err(post("/auth/token/extend", token, token_id).json())


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


def add_push_task(config, push_configs, ttl: int = None,
                  token: Union[bytes, str] = None, token_id: int = None):
    data = {'config': dumps(config), 'push_configs': dumps(push_configs)}
    if ttl is not None:
        data['ttl'] = f"{ttl}"
    return check_err(post("push/add", token, token_id, data).json())


def change_push_task(id: int, config=None, push_configs=None, ttl: int = None,
                     token: Union[bytes, str] = None, token_id: int = None):
    data = {'id': f"{id}"}
    if config is not None:
        data['config'] = dumps(config)
    if push_configs is not None:
        data['push_configs'] = dumps(push_configs)
    if ttl is not None:
        data['ttl'] = f"{ttl}"
    return check_err(post("push/change", token, token_id, data).json())


def get_push_task(id: int, token: Union[bytes, str] = None,
                  token_id: int = None):
    return check_err(post("push/get", token, token_id, {"id": f"{id}"}).json())


def test_push_task(config, push_configs, test_send_mode: Union[str, int],
                   token: Union[bytes, str] = None, token_id: int = None):
    data = {'config': dumps(config), 'push_configs': dumps(
        push_configs), 'test_send_mode': dumps(test_send_mode)}
    return check_err(post("push/test", token, token_id, data).json())
