from argparse import ArgumentParser
import asyncio
from json import load
import sys
from traceback import print_exc
try:
    from dateutil.parser import parse
    have_dateutil = True
except ImportError:
    print('Warning: python-dateutil not found. -s and -e only accept integer now.')  # noqa: E501
    have_dateutil = False
from tdlib import TdLib


def tparse(s: str) -> int:
    try:
        return int(s)
    except Exception:
        if have_dateutil:
            return round(parse(s).timestamp())
        else:
            raise ValueError()


async def get_chat_id_from_name(lib: TdLib, name: str) -> int:
    re = await lib.searchChatsOnServer(name)
    if re is None:
        raise ValueError('Can not found chat.')
    le = len(re['chat_ids'])
    if le == 0:
        re = await lib.searchPublicChats(name)
        if re is None:
            raise ValueError('Can not search public chats.')
        le = len(re['chat_ids'])
        if le == 0:
            raise ValueError('No chat found.')
    if le == 1:
        return re['chat_ids'][0]
    else:
        raise NotImplementedError('Multiply chat is returned.')


async def main(lib: TdLib, arg):
    with open(arg.config, 'r', encoding='UTF-8') as f:
        se = load(f)
    if not await lib.login(se['TdlibParameters'], se['encryption_key'],
                           se.get("proxy"), se.get("phone_number")):
        raise ValueError('Can not login')
    chat_id = arg.chat_id if arg.chat_id is not None else await get_chat_id_from_name(lib, arg.chat_name)  # noqa: E501
    chat = await lib.getChat(chat_id)
    if chat is None:
        print('Chat not found.')
        return -1
    print('Chat information:')
    print(f"Chat ID: {chat['id']}")
    print(f"Chat Title: {chat['title']}")
    print(f"Chat Type: {chat['type']}")
    yes = False
    if not yes:
        inp = input('Do you want to delete messages in this chat?(y/n)')
        if inp[0].lower() == 'y':
            yes = True
    if not yes:
        return 0
    re = await lib.deleteAllMyMessageInChat(chat_id, arg.start_time, arg.end_time)  # noqa: E501
    print(re)
    return 0 if re else -1


p = ArgumentParser(description='Delete all my messages in a chat.', add_help=True)  # noqa: E501
p.add_argument('-c', '--config', default='tdlib.json', metavar='CONFIG', dest='config', help='Specify the location of config file. Default: tdlib.json')  # noqa: E501
p.add_argument('chat_id', nargs='?', type=int, help="Specify the chat's ID.")
p.add_argument('-n', '--chat-name', help="Specify chat's name. Will used if chat_id is not sepcified.", metavar='NAME', dest='chat_name')  # noqa: E501
p.add_argument('-s', '--start-time', type=tparse, metavar='TIME', help="The messages which are sended before this time will not be deleted.", dest='start_time')  # noqa: E501
p.add_argument('-e', '--end-time', type=tparse, metavar='TIME', help="The messages which are sended after this time will not be deleted.", dest="end_time")  # noqa: E501
arg = p.parse_intermixed_args()
if arg.chat_id is None and arg.chat_name is None:
    raise ValueError('chat_id or chat_name is needed.')
try:
    with TdLib() as lib:
        re = asyncio.run(main(lib, arg))
    sys.exit(re)
except Exception:
    print_exc()
    sys.exit(-1)
