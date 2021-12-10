import asyncio
from ctypes import CDLL, c_char_p, c_double, c_int, c_void_p
from ctypes.util import find_library
import sys
from json import dumps, loads
from threading import Thread
from traceback import print_exc
from random import random
from getpass import getpass
from typing import List


tdjson_path = find_library('tdjson') or 'tdjson.dll'
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


class TdLib:
    def __init__(self) -> None:
        self._initalized = False
        self._destoried = False
        self._db_initalized = False
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
        self._destoried = True
        del self._re
        del self._rel

    async def _send(self, data):
        extra = random()
        data['@extra'] = extra
        data = dumps(data, ensure_ascii=False).encode()
        _td_json_client_send(self._client_id, data)
        while True:
            if extra in self._re:
                re = self._re.pop(extra)
                return re
            await asyncio.sleep(0.1)

    def _update(self):
        result: bytes = _td_json_client_receive(self._client_id, 1.0)
        if result:
            re = loads(result.decode())
            if '@extra' in re:
                self._re[re['@extra']] = re
            else:
                self._rel.append(re)

    async def addProxy(self, server, port, enable, type):
        while not self._db_initalized:
            await asyncio.sleep(0.1)
        return await self._send({"@type": "addProxy", "server": server,
                                 "port": port, "enable": enable,
                                 "type": type})

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

    async def deleteAllMyMessageInChat(self, chat_id: int,
                                       start_time: int = None,
                                       end_time: int = None):
        uid = await self.getUid()
        messages = await self.searchChatMessages(chat_id, sender_user_id=uid,
                                                 limit=100)
        if messages is None:
            return False
        while len(messages['messages']) != 0:
            last_mid = messages['messages'][-1]['id']
            mids = []
            for m in messages['messages']:
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
                    print(f"Add {m['id']} to delete list. ({m['date']})")
                    mids.append(m['id'])
            if not await self.deleteMessages(chat_id, mids):
                raise ValueError('Can not delete messages.')
            messages = await self.searchChatMessages(
                chat_id, sender_user_id=uid, from_message_id=last_mid,
                limit=100)
            if messages is None:
                return False
        return True

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

    async def deleteMessages(self, chat_id: int, message_ids: List[int],
                             revoke: bool = True):
        re = await self._send({"@type": "deleteMessages", "chat_id": chat_id,
                               "message_ids": message_ids, "revoke": revoke})
        if re['@type'] == 'ok':
            return True
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return False

    async def enableProxy(self, proxy_id):
        re = await self._send({"@type": "enableProxy", "proxy_id": proxy_id})
        if re['@type'] == 'ok':
            return True
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return False

    async def getMe(self):
        re = await self._send({"@type": "getMe"})
        if re['@type'] == 'user':
            return re
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return None

    async def getProxies(self):
        while not self._db_initalized:
            await asyncio.sleep(0.1)
        return await self._send({"@type": "getProxies"})

    async def getUid(self) -> int:
        if not hasattr(self, "_uid"):
            self._uid = (await self.getMe())['id']
        return self._uid

    async def login(self, parameters, encryption_key, proxy, phone_number):
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
                return True
            else:
                raise ValueError("Unknown authorization_state", state)

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
            raise ValueError('Both chat and user is supported.')
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

    async def setTdlibParameters(self, se):
        re = await self._send({"@type": "setTdlibParameters",
                               "parameters": se})
        if re['@type'] == 'ok':
            return True
        else:
            if re['@type'] == 'error':
                print(f"{re['code']} {re['message']}")
            return False