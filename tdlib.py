import asyncio
from base64 import b64encode
from ctypes import CDLL, c_char_p, c_double, c_int, c_void_p
from ctypes.util import find_library
from enum import Enum
from getpass import getpass
from json import dumps, loads, JSONDecoder, JSONEncoder
from random import random
import sys
from threading import Thread
from traceback import print_exc
from typing import List, Union


tdjson_path = find_library('tdjson')
if tdjson_path is None:
    print("Can't find 'tdjson' library")
    sys.exit(-1)
tdjson = CDLL(tdjson_path)
_td_json_client_create = tdjson.td_json_client_create
_td_json_client_create.restype = c_void_p
_td_json_client_create.argtypes = []
_td_json_client_send = tdjson.td_json_client_send
_td_json_client_send.restype = None
_td_json_client_send.argtypes = [c_void_p, c_char_p]
_td_json_client_destroy = tdjson.td_json_client_destroy
_td_json_client_destroy.restype = None
_td_json_client_destroy.argtypes = [c_void_p]
_td_receive = tdjson.td_receive
_td_receive.restype = c_char_p
_td_receive.argtypes = [c_double]
_td_send = tdjson.td_send
_td_send.restype = None
_td_send.argtypes = [c_int, c_char_p]
_td_execute = tdjson.td_execute
_td_execute.restype = c_char_p
_td_execute.argtypes = [c_char_p]
_td_json_client_receive = tdjson.td_json_client_receive
_td_json_client_receive.restype = c_char_p
_td_json_client_receive.argtypes = [c_void_p, c_double]


def td_execute(query):
    query = dumps(query, ensure_ascii=False, separators=(',', ':')).encode()
    result = _td_execute(query)
    if result:
        result = loads(result.decode())
    return result


if td_execute({'@type': 'setLogVerbosityLevel', 'new_verbosity_level': 1, '@extra': 1.1111111})['@type'] != 'ok':  # noqa: E501
    print('Can not set log level to error level.')


class UpdateThread(Thread):
    def __init__(self, tdlib) -> None:
        self._tdlib = tdlib
        self._need_killed = False
        Thread.__init__(self)

    def kill(self) -> None:
        self._need_killed = True

    async def killed(self):
        while True:
            if not self.is_alive():
                return
            await asyncio.sleep(1)

    def run(self) -> None:
        while True:
            try:
                self._tdlib._update()
                if self._need_killed:
                    return
            except Exception:
                print_exc()


class ChatType:
    def __iter__(self):
        return self.to_dict().items().__iter__()

    def to_dict(self) -> dict:
        pass

    def __repr__(self) -> str:
        d = self.to_dict()
        if d is None:
            m = ''
        else:
            typ = d['@type'][8:]
            d.pop('@type')
            m = f"Type={typ} Data={d}"
        return f"<{self.__class__.__module__}.{self.__class__.__name__} {m}>"

    def __str__(self):
        d = self.to_dict()
        if d is None:
            return ''
        return d['@type'][8:]


class ChatTypeBasicGroup(ChatType):
    def __init__(self, value):
        if isinstance(value, dict):
            if value['@type'] == 'chatTypeBasicGroup':
                self.basic_group_id = int(value['basic_group_id'])
                return
        raise ValueError(f'Unknown value: {value}')

    def to_dict(self):
        return {"@type": "chatTypeBasicGroup",
                "basic_group_id": self.basic_group_id}


class ChatTypePrivate(ChatType):
    def __init__(self, value):
        if isinstance(value, dict):
            if value['@type'] == 'chatTypePrivate':
                self.user_id = int(value['user_id'])
                return
        raise ValueError(f'Unknown value: {value}')

    def to_dict(self):
        return {"@type": 'chatTypePrivate', 'user_id': self.user_id}


class ChatTypeSecret(ChatType):
    def __init__(self, value):
        if isinstance(value, dict):
            if value['@type'] == 'chatTypeSecret':
                self.secret_chat_id = int(value['secret_chat_id'])
                self.user_id = int(value['user_id'])
                return
        raise ValueError(f'Unknown value: {value}')

    def to_dict(self):
        return {"@type": "chatTypeSecret",
                "secret_chat_id": self.secret_chat_id, "user_id": self.user_id}


class ChatTypeSupergroup(ChatType):
    def __init__(self, value):
        if isinstance(value, dict):
            if value['@type'] == 'chatTypeSupergroup':
                self.supergroup_id = int(value['supergroup_id'])
                self.is_channel = bool(value['is_channel'])
                return
        raise ValueError(f'Unknown value: {value}')

    def to_dict(self):
        return {"@type": "chatTypeSupergroup",
                "supergroup_id": self.supergroup_id,
                "is_channel": self.is_channel}


def parse_chat_type(d):
    if d['@type'].startswith('chatType'):
        typ = 'C' + d['@type'][1:]
        return globals()[typ](d)
    raise ValueError(f'Unknown value: {d}')


class TextParseMode(Enum):
    HTML = 0
    MarkDown = 1

    def __iter__(self):
        return self.to_dict().items().__iter__()

    def to_dict(self):
        if self._value_ == 0:
            return {"@type": "textParseModeHTML"}
        elif self._value_ == 1:
            return {"@type": "textParseModeMarkdown"}

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, dict):
            if value['@type'] == 'textParseModeHTML':
                return cls(0)
            elif value['@type'] == 'textParseModeMarkdown':
                return cls(1)
        raise ValueError(f'Unknown value: {value}')


class MessageForwardOrigin:
    def __iter__(self):
        return self.to_dict().items().__iter__()

    def to_dict(self) -> dict:
        pass

    def __repr__(self) -> str:
        d = self.to_dict()
        if d is None:
            m = ''
        else:
            typ = d['@type'][20:]
            d.pop('@type')
            m = f"Type={typ} Data={d}"
        return f"<{self.__class__.__module__}.{self.__class__.__name__} {m}>"

    def __str__(self):
        d = self.to_dict()
        if d is None:
            return ''
        return d['@type'][20:]


class MessageForwardOriginChannel(MessageForwardOrigin):
    def __init__(self, v):
        if isinstance(v, dict):
            if v['@type'] == 'messageForwardOriginChannel':
                self.chat_id = v['chat_id']
                self.message_id = v['message_id']
                self.author_signature = v['author_signature']
                return
        raise ValueError(f'Unknown value: {v}')

    def to_dict(self):
        return {"@type": 'messageForwardOriginChannel',
                'chat_id': self.chat_id, 'message_id': self.message_id,
                'author_signature': self.author_signature}


class MessageForwardOriginChat(MessageForwardOrigin):
    def __init__(self, v):
        if isinstance(v, dict):
            if v['@type'] == 'messageForwardOriginChat':
                self.sender_chat_id = v['sender_chat_id']
                self.author_signature = v['author_signature']
                return
        raise ValueError(f'Unknown value: {v}')

    def to_dict(self):
        return {"@type": "messageForwardOriginChat",
                "sender_chat_id": self.sender_chat_id,
                "author_signature": self.author_signature}


class MessageForwardOriginHiddenUser(MessageForwardOrigin):
    def __init__(self, v):
        if isinstance(v, dict):
            if v['@type'] == 'messageForwardOriginHiddenUser':
                self.sender_name = v['sender_name']
                return
        raise ValueError(f'Unknown value: {v}')

    def to_dict(self):
        return {"@type": "messageForwardOriginHiddenUser",
                "sender_name": self.sender_name}


class MessageForwardOriginMessageImport(MessageForwardOrigin):
    def __init__(self, v):
        if isinstance(v, dict):
            if v['@type'] == 'messageForwardOriginMessageImport':
                self.sender_name = v['sender_name']
                return
        raise ValueError(f'Unknown value: {v}')

    def to_dict(self):
        return {"@type": "messageForwardOriginMessageImport",
                "sender_name": self.sender_name}


class MessageForwardOriginUser(MessageForwardOrigin):
    def __init__(self, v):
        if isinstance(v, dict):
            if v['@type'] == 'messageForwardOriginUser':
                self.sender_user_id = v['sender_user_id']
                return
        raise ValueError(f'Unknown value: {v}')

    def to_dict(self):
        return {"@type": "messageForwardOriginUser",
                "sender_user_id": self.sender_user_id}


def parse_message_forward_orgin(d):
    if d['@type'].startswith('messageForwardOrigin'):
        typ = 'M' + d['@type'][1:]
        return globals()[typ](d)
    raise ValueError(f'Unknown value: {d}')


def json_object_hook(value):
    try:
        if isinstance(value, dict):
            if '@type' in value:
                if value['@type'].startswith('chatType'):
                    return parse_chat_type(value)
                elif value['@type'].startswith('textParseMode'):
                    return TextParseMode(value)
                elif value['@type'].startswith('messageForwardOrigin'):
                    return parse_message_forward_orgin(value)
                elif value['@type'] == 'message':
                    value['media_album_id'] = int(value['media_album_id'])
                elif value['@type'] == 'getStickerSet':
                    value['set_id'] = int(value['set_id'])
                elif value['@type'] == 'stickerSet':
                    value['id'] = int(value['id'])
    except Exception:
        print_exc()
        return value
    return value


class TdLibJSONDecoder(JSONDecoder):
    def __init__(self, *k, **kw) -> None:
        super().__init__(*k, object_hook=json_object_hook, **kw)


class TdLibJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, (ChatType, TextParseMode, MessageForwardOrigin)):
            return dict(o)
        elif isinstance(o, bytes):
            return b64encode(o).decode()
        elif isinstance(o, dict):
            if '@type' in o:
                if o['@type'] == 'message':
                    if 'media_album_id' in o:
                        o['media_album_id'] = str(o['media_album_id'])
                elif o['@type'] == 'getStickerSet':
                    if 'set_id' in o:
                        o['set_id'] = str(o['set_id'])
                elif o['@type'] == 'stickerSet':
                    if 'id' in o:
                        o['id'] = str(o['id'])
        return super().default(o)


class TdLib:
    def __init__(self, verbose: bool = False, maxCache: int = None) -> None:
        self._initalized = False
        self._destoried = False
        self._db_initalized = False
        self._logined = False
        self._v = verbose
        self._maxCache = 1000
        if maxCache is not None:
            if maxCache < 100:
                raise ValueError('At least cache 100 messages.')
            self._maxCache = maxCache
        self._e = 0
        self._re = {}
        self._rel = []

    def __enter__(self):
        if self._destoried:
            raise ValueError('Already destoried.')
        self._e += 1
        if not self._initalized:
            self._client_id = _td_json_client_create()
            if not self._client_id:
                raise ValueError('Can not create tdlib client.')
            self._thread = UpdateThread(self)
            self._thread.start()
        return self

    def __exit__(self, type, value, tb):
        if self._destoried:
            raise ValueError('Already destoried.')
        self._e -= 1
        if self._e == 0:
            asyncio.run(self.__destory())

    async def __destory(self):
        self._thread.kill()
        await self._thread.killed()
        _td_json_client_destroy(self._client_id)
        self._client_id = 0
        self._destoried = True
        if self._v:
            le1 = len(self._re)
            le2 = len(self._rel)
            print(f"There are {le1 + le2} ({le1} + {le2}) messages in cache.")
        del self._re
        del self._rel

    async def _send(self, data) -> dict:
        extra = random()
        data['@extra'] = extra
        en = TdLibJSONEncoder(ensure_ascii=False)
        data = en.encode(data).encode()
        _td_json_client_send(self._client_id, data)
        while True:
            if extra in self._re:
                re = self._re.pop(extra)
                return re
            await asyncio.sleep(0.1)

    def _update(self):
        result: bytes = _td_json_client_receive(self._client_id, 1.0)
        if result:
            de = TdLibJSONDecoder()
            re = de.decode(result.decode())
            if self._v:
                if '@type' in re:
                    print(f'Get a new message. Message type: {re["@type"]}')
            if '@extra' in re:
                self._re[re['@extra']] = re
            else:
                while len(self._rel) >= self._maxCache:
                    m = self._rel.pop(0)
                    if self._v:
                        t = m['@type'] if '@type' in m else 'Unknown'
                        print(f'Discard a message in cache. Message type: {t}')
                self._rel.append(re)

    async def addProxy(self, server, port, enable, type):
        while not self._db_initalized:
            await asyncio.sleep(0.1)
        return await self._send({"@type": "addProxy", "server": server,
                                 "port": port, "enable": enable,
                                 "type": type})

    async def addStickerToSet(self, user_id: int, name: str, sticker):
        re = await self._send({"@type": "addStickerToSet", "user_id": user_id,
                               "name": name, "sticker": sticker})
        if re['@type'] == 'stickerSet':
            return re
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return None

    async def checkAuthenticationCode(self, code: str):
        re = await self._send({"@type": "checkAuthenticationCode",
                               "code": code})
        if re['@type'] == 'ok':
            return True
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return False

    async def checkDatabaseEncryptionKey(self, encryption_key):
        re = await self._send({"@type": "checkDatabaseEncryptionKey",
                               "encryption_key": encryption_key})
        if re['@type'] == 'ok':
            return True
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return False

    async def checkAuthenticationPassword(self, password: str):
        re = await self._send({"@type": "checkAuthenticationPassword",
                               "password": password})
        if re['@type'] == 'ok':
            return True
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return False

    async def checkAuthenticationBotToken(self, token: str):
        re = await self._send({"@type": "checkAuthenticationBotToken",
                               "token": token})
        if re['@type'] == 'ok':
            return True
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return False

    async def createNewStickerSet(self, title: str, name: str, stickers,
                                  is_masks: bool = False, source: str = '',
                                  user_id: int = 0):
        re = await self._send({"@type": "createNewStickerSet", "title": title,
                               "name": name, "stickers": stickers,
                               "is_masks": is_masks, "source": source,
                               "user_id": user_id})
        if re['@type'] == 'stickerSet':
            return re
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return None

    async def deleteAllMyMessageInChat(self, chat_id: int,
                                       start_time: int = None,
                                       end_time: int = None,
                                       verbose: bool = True,
                                       excludes: List[int] = None):
        uid = await self.getUid()
        messages = await self.searchChatMessages(chat_id, sender_user_id=uid,
                                                 limit=100)
        c = 0
        if messages is None:
            return None
        while len(messages['messages']) != 0:
            last_mid = messages['messages'][-1]['id']
            mids = []
            for m in messages['messages']:
                if excludes is not None:
                    if m['id'] in excludes:
                        continue
                need_deleted = False
                if start_time is None and end_time is None:
                    need_deleted = True
                elif start_time is None:
                    if m['date'] <= end_time:
                        need_deleted = True
                elif end_time is None:
                    if m['date'] >= start_time:
                        need_deleted = True
                else:
                    if m['date'] >= start_time and m['date'] <= end_time:
                        need_deleted = True
                if need_deleted and m['can_be_deleted_for_all_users']:
                    if verbose:
                        print(f"Add {m['id']} to delete list. ({m['date']})")
                    mids.append(m['id'])
            if not await self.deleteMessages(chat_id, mids):
                raise ValueError('Can not delete messages.')
            c += len(mids)
            messages = await self.searchChatMessages(
                chat_id, sender_user_id=uid, from_message_id=last_mid,
                limit=100)
            if messages is None:
                return None
        return c

    async def deleteChatHistory(self, chat_id: int,
                                remove_from_chat_list: bool = False,
                                revoke: bool = False):
        re = await self._send({"@type": "deleteChatHistory",
                               "chat_id": chat_id,
                               "remove_from_chat_list": remove_from_chat_list,
                               "revoke": revoke})
        if re['@type'] == 'ok':
            return True
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return False

    async def deleteMessages(self, chat_id: int,
                             message_ids: Union[List[int], int],
                             revoke: bool = True):
        if isinstance(message_ids, int):
            message_ids = [message_ids]
        re = await self._send({"@type": "deleteMessages", "chat_id": chat_id,
                               "message_ids": message_ids, "revoke": revoke})
        if re['@type'] == 'ok':
            return True
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return False

    async def editMessageText(self, chat_id: int, message_id: int, text: str,
                              parse_mode: TextParseMode = None, entities=None,
                              disable_web_page_preview: bool = False,
                              clear_draft: bool = False):
        if parse_mode is not None and entities is not None:
            raise ValueError('Bot parse_mode and entities are not supported.')
        if parse_mode is not None:
            mes = await self.parseTextEntities(text, parse_mode)
            if mes is None:
                return None
            entities = mes['entities']
            text = mes['text']
        elif entities is None:
            entities = await self.getTextEntities(text)
            if entities is None:
                return None
            entities = entities['entities']
        d = {'@type': 'editMessageText', 'chat_id': chat_id,
             'message_id': message_id, 'input_message_content': {
                 '@type': 'inputMessageText',
                 'text': {'@type': 'formattedText', 'text': text,
                          'entities': entities},
                 'disable_web_page_preview': disable_web_page_preview,
                 'clear_draft': clear_draft
             }}
        re = await self._send(d)
        if re['@type'] == 'message':
            return re
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return None

    async def enableProxy(self, proxy_id):
        re = await self._send({"@type": "enableProxy", "proxy_id": proxy_id})
        if re['@type'] == 'ok':
            return True
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return False

    async def getChat(self, chat_id: int):
        re = await self._send({"@type": "getChat", "chat_id": chat_id})
        if re['@type'] == 'chat':
            return re
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return None

    async def getChatHistory(self, chat_id: int, from_message_id: int = None,
                             offset: int = None, limit: int = 20,
                             only_local: bool = False):
        d = {"@type": 'getChatHistory', "chat_id": chat_id, "limit": limit,
             "only_local": only_local}
        if from_message_id is not None:
            d['from_message_id'] = from_message_id
        if offset is not None:
            d['offset'] = offset
        re = await self._send(d)
        if re['@type'] == 'messages':
            return re
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return None

    async def getMe(self):
        re = await self._send({"@type": "getMe"})
        if re['@type'] == 'user':
            return re
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return None

    async def getMessage(self, chat_id: int, message_id: int):
        re = await self._send({"@type": "getMessage", "chat_id": chat_id,
                               "message_id": message_id})
        if re['@type'] == 'message':
            return re
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return None

    async def getMessageLink(self, chat_id: int, message_id: int,
                             media_timestamp: int = 0, for_album: bool = False,
                             for_comment: bool = False):
        re = await self._send({"@type": "getMessageLink", "chat_id": chat_id,
                               "message_id": message_id,
                               "media_timestamp": media_timestamp,
                               "for_album": for_album,
                               "for_comment": for_comment})
        if re['@type'] == 'messageLink':
            return re
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return None

    async def getProxies(self):
        while not self._db_initalized:
            await asyncio.sleep(0.1)
        return await self._send({"@type": "getProxies"})

    async def getStickerSet(self, set_id: int):
        re = await self._send({"@type": "getStickerSet", "set_id": set_id})
        if re['@type'] == 'stickerSet':
            return re
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return None

    async def getTextEntities(self, text: str):
        re = await self._send({"@type": "getTextEntities", "text": text})
        if re['@type'] == 'textEntities':
            return re
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return None

    async def getUid(self) -> int:
        if not hasattr(self, "_uid"):
            self._uid = (await self.getMe())['id']
        return self._uid

    async def getUsername(self) -> str:
        if not hasattr(self, "_username"):
            self._username = (await self.getMe())['username']
        return self._username

    async def login(self, parameters, encryption_key, proxy, phone_number=None,
                    bot_token=None):
        while True:
            re = await self.receive('updateAuthorizationState')
            state = re['authorization_state']
            if state['@type'] == 'authorizationStateWaitTdlibParameters':
                pa = {"use_message_database": True,
                      "system_language_code": "en",
                      "device_model": "Desktop",
                      "application_version": "1.0.0",
                      "enable_storage_optimizer": True,
                      'use_secret_chats': True}
                pa.update(parameters)
                if not await self.setTdlibParameters(pa):
                    raise ValueError("Can not change Tdlib's parameters.")
            elif state['@type'] == 'authorizationStateWaitEncryptionKey':
                if not await self.checkDatabaseEncryptionKey(encryption_key):
                    raise ValueError('Checks the database encryption key failed.')  # noqa: E501
                self._db_initalized = True
                if proxy is not None:
                    if not await self.setProxy(proxy['server'], proxy['port'], proxy['type']):  # noqa: E501
                        raise ValueError('Can not set proxy.')
            elif state['@type'] == 'authorizationStateWaitPhoneNumber':
                if bot_token is not None:
                    if not await self.checkAuthenticationBotToken(bot_token):
                        raise ValueError('Invalid bot token')
                    continue
                if phone_number is None:
                    phone_number = input('Please input your phone number:')
                if not await self.setAuthenticationPhoneNumber(phone_number):
                    raise ValueError('Can not set phone number.')
            elif state['@type'] == 'authorizationStateWaitCode':
                code = input('Please enter the authentication code you received: ')  # noqa: E501
                if not await self.checkAuthenticationCode(code):
                    raise ValueError('Incorrect code.')
            elif state['@type'] == 'authorizationStateWaitPassword':
                paw = getpass("Please enter your password: ")
                if not await self.checkAuthenticationPassword(paw):
                    raise ValueError('Incorrect passwrod.')
            elif state['@type'] == 'authorizationStateReady':
                self._logined = True
                return True
            else:
                raise ValueError("Unknown authorization_state", state)

    async def optimizeStorage(self, size: int = -1, ttl: int = -1,
                              count: int = -1, immunity_delay: int = -1,
                              file_types: list = None,
                              chat_ids: List[int] = None,
                              exclude_chat_ids: List[int] = None,
                              return_deleted_file_statistics: bool = False,
                              chat_limit: int = None):
        d = {"@type": "optimizeStorage", "size": size, "ttl": ttl,
             "count": count, "immunity_delay": immunity_delay,
             "return_deleted_file_statistics": return_deleted_file_statistics}
        if file_types is not None:
            d['file_types'] = file_types
        if chat_ids is not None:
            d['chat_ids'] = chat_ids
        if exclude_chat_ids is not None:
            d['exclude_chat_ids'] = exclude_chat_ids
        if chat_limit is not None:
            d['chat_limit'] = chat_limit
        re = await self._send(d)
        if re['@type'] == 'storageStatistics':
            return re
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return None

    async def parseMarkdown(self, text: str):
        re = await self._send({"@type": "parseMarkdown", "text": text})
        if re['@type'] == 'formattedText':
            return re
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return None

    async def parseTextEntities(self, text: str, parse_mode: TextParseMode):
        re = await self._send({"@type": "parseTextEntities", "text": text,
                               "parse_mode": parse_mode})
        if re['@type'] == 'formattedText':
            return re
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return None

    async def receive(self, type: str = None):
        while True:
            if len(self._rel) > 0:
                if type is None:
                    return self._rel.pop(0)
                else:
                    for i in self._rel:
                        if '@type' in i and i['@type'] == type:
                            self._rel.remove(i)
                            return i
            await asyncio.sleep(0.1)

    async def searchChatMessages(self, chat_id: int, query: str = None,
                                 sender_chat_id: int = None,
                                 sender_user_id: int = None,
                                 from_message_id: int = None,
                                 offset: int = None, limit: int = 20,
                                 filter=None, message_thread_id: int = None):
        d = {"@type": "searchChatMessages", "chat_id": chat_id, "limit": limit}
        if query is not None:
            d['query'] = query
        if sender_chat_id is not None and sender_user_id is not None:
            raise ValueError('Both chat and user is not supported.')
        if sender_chat_id is not None:
            d['sender_id'] = {'@type': "messageSenderChat",
                              "chat_id": sender_chat_id}
        elif sender_user_id is not None:
            d['sender_id'] = {'@type': "messageSenderUser",
                              'user_id': sender_user_id}
        if from_message_id is not None:
            d['from_message_id'] = from_message_id
        if offset is not None:
            d['offset'] = offset
        if filter is not None:
            d['filter'] = filter
        if message_thread_id is not None:
            d['message_thread_id'] = message_thread_id
        re = await self._send(d)
        if re['@type'] == 'messages':
            return re
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return None

    async def searchChats(self, query: str, limit: int = 20):
        re = await self._send({"@type": "searchChats", "query": query,
                               "limit": limit})
        if re['@type'] == 'chats':
            return re
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return None

    async def searchChatsOnServer(self, query: str, limit: int = 20):
        re = await self._send({"@type": "searchChatsOnServer", "query": query,
                               "limit": limit})
        if re['@type'] == 'chats':
            return re
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return None

    async def searchPublicChats(self, query: str):
        re = await self._send({"@type": "searchPublicChats", "query": query})
        if re['@type'] == 'chats':
            return re
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return None

    async def searchStickerSet(self, name: str):
        re = await self._send({"@type": "searchStickerSet", "name": name})
        if re['@type'] == 'stickerSet':
            return re
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return None

    async def sendMessage(self, chat_id: int, content,
                          message_thread_id: int = 0,
                          reply_to_message_id: int = 0, options=None,
                          reply_markup=None):
        d = {"@type": "sendMessage", "chat_id": chat_id,
             "input_message_content": content}
        if message_thread_id != 0:
            d['message_thread_id'] = message_thread_id
        if reply_to_message_id != 0:
            d['reply_to_message_id'] = reply_to_message_id
        if options is not None:
            d['options'] = options
        if reply_markup is not None:
            d['reply_markup'] = reply_markup
        re = await self._send(d)
        if re['@type'] == 'message':
            return re
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return None

    async def sendTextMessage(self, chat_id: int, text: str,
                              mode: TextParseMode = None,
                              disable_web_page_preview: bool = False,
                              clear_draft: bool = False, **kw):
        mes = {'@type': 'inputMessageText', 'clear_draft': clear_draft,
               'disable_web_page_preview': disable_web_page_preview}
        if mode is None:
            t = {"@type": "formattedText", "text": text}
            t['entities'] = (await self.getTextEntities(text))['entities']
            if t['entities'] is None:
                return None
        else:
            mes['text'] = await self.parseTextEntities(text, mode)
            if mes['text'] is None:
                return None
        mes['text'] = t
        return await self.sendMessage(chat_id, mes, **kw)

    async def setAuthenticationPhoneNumber(self, phone_number, settings=None):
        sett = {"@type": "phoneNumberAuthenticationSettings",
                "allow_flash_call": False,
                "allow_missed_call": False,
                "is_current_phone_number": False,
                "allow_sms_retriever_api": False}
        if settings is not None:
            sett.update(settings)
        re = await self._send({"@type": "setAuthenticationPhoneNumber",
                               "phone_number": str(phone_number),
                               "settings": sett})
        if re['@type'] == 'ok':
            return True
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return False

    async def setDatabaseEncryptionKey(self,
                                       new_encryption_key: Union[str, bytes]):
        re = await self._send({"@type": "setDatabaseEncryptionKey", "new_encryption_key": new_encryption_key})  # noqa: E501
        if re['@type'] == 'ok':
            return True
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return False

    async def setProxy(self, server, port, type):
        while not self._db_initalized:
            await asyncio.sleep(0.1)
        proxies = await self.getProxies()
        for i in proxies['proxies']:
            if i['server'] == server and i['port'] == port:
                ok = True
                for k in type:
                    if k in i['type']:
                        if type[k] != i['type']:
                            ok = False
                            break
                    else:
                        ok = False
                        break
                if ok:
                    print(i)
                    if not i['is_enabled']:
                        await self.enableProxy(i['id'])
                    return True
        re = await self.addProxy(server, port, True, type)
        if re['@type'] == 'proxy':
            return True
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return False

    async def setStickerSetThumbnail(self, user_id: int, name: str, thumb):
        re = await self._send({"@type": "setStickerSetThumbnail",
                               "user_id": user_id, "name": name,
                               "thumbnail": thumb})
        if re['@type'] == 'stickerSet':
            return re
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return None

    async def setTdlibParameters(self, se):
        re = await self._send({"@type": "setTdlibParameters",
                               "parameters": se})
        if re['@type'] == 'ok':
            return True
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return False
