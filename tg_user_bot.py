from argparse import ArgumentParser
import asyncio
from html import escape
from json import load
from re import I, compile
from traceback import format_exc
from typing import List
from tdlib import (
    MessageForwardOriginChannel,
    MessageForwardOriginChat,
    MessageForwardOriginHiddenUser,
    MessageForwardOriginMessageImport,
    MessageForwardOriginUser,
    TdLib,
    TextParseMode,
)
from time import time
from util import commandLineToArgv, timeToStr, tparse
import requests


USERNAME_REG = compile(r'^[0-9a-z_]+$', I)


def validate_sticker_set_name(n: str) -> str:
    if len(n) == 0 or len(n) > 64:
        raise ValueError('1-64 characters')
    r = USERNAME_REG.search(n)
    if r is None or n.startswith('_') or n.endswith('_'):
        raise ValueError('Can contain only English letters, digits and underscores.')  # noqa: E501
    return n


def validate_sticker_set_title(n: str) -> str:
    if len(n) == 0 or len(n) > 64:
        raise ValueError('1-64 characters is needed.')
    return n


class MyArgParser(ArgumentParser):
    def error(self, message: str):
        raise ValueError(message)

    def exit(self, status, message):
        pass


cnss = MyArgParser('-createnewstickerset', add_help=False, description="Create a new sticker set.", epilog="Note: Reply to a sticker message is needed.")  # noqa: E501
cnss.add_argument('name', help="Sticker set name. Can contain only English letters, digits and underscores. 1-64 characters. Must ended with _by_<botname> if create with a bot account", type=validate_sticker_set_name)  # noqa: E501
cnss.add_argument('title', help="Sticker set title. 1-64 characters", type=validate_sticker_set_title)  # noqa: E501
cnss.add_argument('source', help='Source of the sticker set', nargs='?', default='')  # noqa: E501
cnss.add_argument('-e', '--emoji', help='Emojis corresponding to the sticker. Can not combined with -A', metavar='EMOJI', dest='emoji')  # noqa: E501
cnss.add_argument('-u', '--user', help='Create with user account. Will have issue when try add sticker to set', action='store_true', dest='user')  # noqa: E501
cnss.add_argument('-a', '--add-suffix', help='Add _by_<botname> automatically', action='store_true', dest='add_suffix')  # noqa: E501
cnss.add_argument('-A', '--all-stickers', help='Add all stickers in the sticker set which replied sticker belongs', action='store_true', dest="all_stickers")  # noqa: E501
asts = MyArgParser('-addstickertoset', add_help=False, description="Add a sticker to a exist sticker set.", epilog="Note: Reply to a sticker message is needed.")  # noqa: E501
asts.add_argument('name', help="Sticker set name. Must ended with _by_<botname>", type=validate_sticker_set_name, nargs='?')  # noqa: E501
asts.add_argument('--id', help='Sticker set ID. Needed if name not specified.', type=int, metavar='ID', dest='id')  # noqa: E501
asts.add_argument('-e', '--emoji', help='Emojis corresponding to the sticker', metavar='EMOJI', dest='emoji')  # noqa: E501
asts.add_argument('-a', '--add-suffix', help='Add _by_<botname> automatically', action='store_true', dest='add_suffix')  # noqa: E501
asts.add_argument('-d', '--delete', help='Delete command message if executed successfully.', action='store_true', dest='delete')  # noqa: E501
damm = MyArgParser('-deleteallmymessages', add_help=False, description='Delete messages in one chat.')  # noqa: E501
damm.add_argument('chat_id', type=int, nargs='?', help="Specify chat's ID.")
damm.add_argument('-n', '--chat-name', help="Specify chat's name. Will used if chat_id is not sepcified.", metavar='NAME', dest='chat_name')  # noqa: E501
damm.add_argument('-s', '--start-time', type=tparse, metavar='TIME', help="The messages which are sended before this time will not be deleted.", dest='start_time')  # noqa: E501
damm.add_argument('-e', '--end-time', type=tparse, metavar='TIME', help="The messages which are sended after this time will not be deleted.", dest="end_time")  # noqa: E501
nbnhhsh = MyArgParser('-nbnhhsh', description='「能不能好好说话？」 拼音首字母缩写翻译工具', add_help=False)  # noqa: E501
nbnhhsh.add_argument('缩写', help='缩写形式')
nbnhhsh.add_argument('-t', '--timeout', help='设置超时时长，单位为秒（默认为 5 秒）', default=5, type=int, metavar='时长', dest='timeout')  # noqa: E501
sm = MyArgParser('-searchmessage', description='Search message in a chat.', add_help=False)  # noqa: E501
sm.add_argument('keyword', help='Sepcify the keyword.')
sm.add_argument('-c', '--chat_id', help='Specify the chat to search.', type=int, metavar='ID', dest='chat_id')  # noqa: E501
sm.add_argument('-m', '--max_searched', help='Specify the maximum count of messages to searched. -1 if unlimited. (Default: 1000)', type=int, default=1000, metavar='COUNT', dest='max_searched')  # noqa: E501
om = MyArgParser('-optimizestorage', description='Optimizes storage usage for tdlib (user bot).', add_help=False)  # noqa: E501
om.add_argument('-h', '--help', help='Print this message.', action='store_true', dest='help')  # noqa: E501
om.add_argument('-s', '--size', help='Limit on the total size of files after deletion, in bytes.', type=int, metavar='BYTES', dest='size')  # noqa: E501
om.add_argument('-t', '--ttl', help='Limit on the time that has passed since the last time a file was accessed (or creation time for some filesystems).', type=int, metavar='TIME', dest='ttl')  # noqa: E501
om.add_argument('-c', '--count', help='Limit on the total count of files after deletion.', type=int, metavar='COUNT', dest='count')  # noqa: E501
om.add_argument('-i', '--immunity_delay', help="The amount of time after the creation of a file during which it can't be deleted, in seconds.", type=int, metavar='TIME', dest='immunity_delay')  # noqa: E501
om.add_argument('-C', '--chat_ids', help='If non-empty, only files from the given chats are considered. Use 0 as chat identifier to delete files not belonging to any chat (e.g., profile photos).', action='append', type=int, metavar='ID', dest='chat_ids')  # noqa: E501
om.add_argument('-e', '--exclude_chat_ids', help='If non-empty, files from the given chats are excluded. Use 0 as chat identifier to exclude all files not belonging to any chat (e.g., profile photos).', action='append', type=int, metavar='ID', dest='exclude_chat_ids')  # noqa: E501
om.add_argument('-r', '--return_deleted_file_statistics', help='Specifiy it if statistics about the files that were deleted must be returned instead of the whole storage usage statistics. Affects only returned statistics.', action='store_true', dest='return_deleted_file_statistics')  # noqa: E501
om.add_argument('--chat_limit', help='The maximum number of chats with the largest storage usage for which separate statistics need to be returned.', type=int, metavar='COUNT', dest='chat_limit')  # noqa: E501
om.add_argument('-R', '--robot', help="Optimize for robot's storage rather than user.", action='store_true', dest='robot')  # noqa: E501


def generateFileInfo(f: dict) -> str:
    m = ''
    if '@type' in f and f['@type'] == 'file':
        m = f"File ID: `{f['id']}`"
        if f['size'] != 0:
            m += f"\nFile Size: `{f['size']}B`"
        elif f['expected_size'] != 0:
            m += f"\nFile Expected Size: `{f['expected_size']}B`"
        if 'remote' in f and f['remote']['@type'] == 'remoteFile':
            rf = f['remote']
            if rf['id'] != '':
                m += f"\nRemote File ID: `{rf['id']}`"
            if rf['unique_id'] != '':
                m += f"\nRemote Unique File ID: `{rf['unique_id']}`"
    return m


async def handle_message_info(lib: TdLib, mes):
    if mes['reply_to_message_id'] == 0:
        re = await lib.editMessageText(mes['chat_id'], mes['id'],
                                       "Reply a message is needed.")
    else:
        nmes = await lib.getMessage(mes['reply_in_chat_id'],
                                    mes['reply_to_message_id'])
        if nmes is None:
            re = await lib.editMessageText(mes['chat_id'], mes['id'],
                                           "Can not get the replied message.")
        else:
            me = f"Message ID: `{nmes['id']}`"
            if nmes['sender_id']['@type'] == 'messageSenderChat':
                me += f"\nSender Chat ID: `{nmes['sender_id']['chat_id']}`"
            elif nmes['sender_id']['@type'] == 'messageSenderUser':
                me += f"\nSender User ID: `{nmes['sender_id']['user_id']}`"
            me += f"\nChat ID: `{nmes['chat_id']}`"
            me += f"\nSend Date: `{timeToStr(nmes['date'])}`"
            if nmes['edit_date'] != 0:
                me += f"\nLast Edited Date: `{timeToStr(nmes['edit_date'])}`"
            if 'forward_info' in nmes:
                fi = nmes['forward_info']
                if fi is not None and fi['@type'] == 'messageForwardInfo':
                    me += "\nForward Infomation:"
                    o = fi['origin']
                    me += f"\nOrigin Sender Type: `{o}`"
                    if isinstance(o, MessageForwardOriginUser):
                        me += f"\nOrigin Sender User ID: `{o.sender_user_id}`"
                    elif isinstance(o, (MessageForwardOriginHiddenUser, MessageForwardOriginMessageImport)):  # noqa: E501
                        me += f"\nOrigin Sender Name: `{o.sender_name}`"
                    elif isinstance(o, MessageForwardOriginChat):
                        me += f"\nOrigin Sender Chat ID: `{o.sender_chat_id}`"
                        if o.author_signature != "":
                            me += f"\nAuthor Signature: `{o.author_signature}`"
                    elif isinstance(o, MessageForwardOriginChannel):
                        me += f"\nOrigin Sender Chat ID: `{o.chat_id}`"
                        me += f"\nOrigin Sender Message ID: `{o.message_id}`"
                        if o.author_signature != "":
                            me += f"\nAuthor Signature: `{o.author_signature}`"
                    me += f"\nOrigin Send Date: `{timeToStr(fi['date'])}`"
                    if fi['public_service_announcement_type'] != '':
                        me += f"\nPublic Service Announcement Type: `{fi['public_service_announcement_type']}`"  # noqa: E501
                    if fi['from_chat_id'] != 0:
                        me += f"\nFrom Chat ID: `{fi['from_chat_id']}`"
                    if fi['from_message_id'] != 0:
                        me += f"\nFrom Message ID: `{fi['from_message_id']}`"
            if 'interaction_info' in nmes:
                ii = nmes['interaction_info']
                if ii is not None and ii['@type'] == 'messageInteractionInfo':
                    me += "\nIteraction Info:"
                    me += f"\nView Count: `{ii['view_count']}`"
                    me += f"\nForward Count: `{ii['forward_count']}`"
            if nmes['reply_in_chat_id'] != 0:
                me += f"\nReply In Chat ID: `{nmes['reply_in_chat_id']}`"
            if nmes['reply_to_message_id'] != 0:
                me += f"\nReply To Message ID: `{nmes['reply_to_message_id']}`"
            if nmes['message_thread_id'] != 0:
                me += f"\nMessage Thread ID: `{nmes['message_thread_id']}`"
            if nmes['via_bot_user_id'] != 0:
                me += f"\nVia Bot User ID: `{nmes['via_bot_user_id']}`"
            if nmes['author_signature'] != '':
                me += f"\nAuthor Signature: `{nmes['author_signature']}`"
            if nmes['media_album_id'] != 0:
                me += f"\nMedia Album ID: `{nmes['media_album_id']}`"
            if nmes['restriction_reason'] != '':
                me += f"\nRestriction Reason: `{nmes['restriction_reason']}`"
            if nmes['content']['@type'] == 'messageSticker':
                st = nmes['content']['sticker']
                me += f"\nSticker Set ID: `{st['set_id']}`"
                me += f"\nSticker Width: `{st['width']}`"
                me += f"\nSticker Height: `{st['height']}`"
                me += f"\nSticker Emoji: `{st['emoji']}`"
                me += f"\nAnimated Sticker: `{st['is_animated']}`"
                me += f"\nMask Sticker: `{st['is_mask']}`"
                if 'sticker' in st and st['sticker'] is not None:
                    me += "\nSticker File Info:"
                    me += "\n" + generateFileInfo(st['sticker'])
            re = await lib.editMessageText(
                mes['chat_id'], mes['id'], me, TextParseMode.MarkDown)
    if re is None:
        print('Can not edit message')


async def handle_create_new_sticker_set(lib: TdLib, robot: TdLib, mes: dict,
                                        argv: List[str]):
    if len(argv) == 1:
        re = await lib.editMessageText(
            mes['chat_id'], mes['id'], f"```\n{cnss.format_help()}\n```",
            TextParseMode.MarkDown)
    else:
        try:
            r = cnss.parse_intermixed_args(argv[1:])
            if r.emoji and r.all_stickers:
                raise ValueError('-e is not supported when -A is specified.')
            if r.add_suffix and not r.user:
                un = await robot.getUsername()
                if not r.name.endswith(f'_by_{un}'):
                    r.name += f'_by_{un}'
                validate_sticker_set_name(r.name)
            if mes['reply_to_message_id'] == 0:
                raise ValueError('Reply a sticker message is needed.')
            nmes = await lib.getMessage(mes['reply_in_chat_id'],
                                        mes['reply_to_message_id'])
            if nmes is None:
                raise ValueError('Can not get the replied message.')
            if nmes['content']['@type'] != 'messageSticker':
                raise ValueError('Reply a sticker message is needed.')
            if r.all_stickers:
                set_id = nmes['content']['sticker']['set_id']
                ss = await lib.getStickerSet(set_id)
                if ss is None:
                    raise ValueError('Can not get sticker set.')
                st = []
                for s in ss['stickers']:
                    if max(s['width'], s['height']) != 512:
                        raise ValueError('Invalid width or height')
                    fid = s['sticker']['remote']['id']
                    if fid == '':
                        raise ValueError("Can not get sticker's file ID.")
                    st.append({"@type": "inputStickerStatic", "sticker": {"@type": "inputFileRemote", "id": fid}, "emojis": s['emoji']})  # noqa: E501
            else:
                width = nmes['content']['sticker']['width']
                height = nmes['content']['sticker']['height']
                if max(width, height) != 512:
                    raise ValueError('Invalid width or height')
                fid = nmes['content']['sticker']['sticker']['remote']['id']
                emoji = nmes['content']['sticker']['emoji'] if r.emoji is None else r.emoji  # noqa: E501
                if fid == '':
                    raise ValueError("The target sticker's file id is empty.")
                st = [{"@type": "inputStickerStatic", "sticker": {"@type": "inputFileRemote", "id": fid}, "emojis": emoji}]  # noqa: E501
            if not r.user and not robot._logined:
                raise ValueError('A bot account is needed. Or add -u to create with user account.')  # noqa: E501
            if r.user:
                r = await lib.createNewStickerSet(r.title, r.name, st, source=r.source)  # noqa: E501
            else:
                uid = await lib.getUid()
                if uid is None:
                    raise ValueError('Can not get User ID.')
                r = await robot.createNewStickerSet(r.title, r.name, st, source=r.source, user_id=uid)  # noqa: E501
            if r is None:
                raise ValueError('Can not create new sticker set.')
            re = await lib.editMessageText(mes['chat_id'], mes['id'], f"Created successfully.\nSticker Set ID: {r['id']}\nhttps://t.me/addstickers/{r['name']}")  # noqa: E501
        except ValueError as e:
            if len(e.args) == 0:
                re = await lib.editMessageText(mes['chat_id'], mes['id'], "Unknown error.")  # noqa: E501
            else:
                re = await lib.editMessageText(mes['chat_id'], mes['id'], f"```\n{cnss.format_usage()}{cnss.prog}: error: {e.args[0] if len(e.args) == 1 else e.args}\n```", TextParseMode.MarkDown)  # noqa: E501
        except Exception:
            re = await lib.editMessageText(mes['chat_id'], mes['id'], f"```\n{format_exc()}\n```", TextParseMode.MarkDown)  # noqa: E501
    if re is None:
        print('Can not edit message')


async def handle_add_sticker_to_set(lib: TdLib, robot: TdLib, mes: dict,
                                    argv: List[str]):
    if len(argv) == 1:
        re = await lib.editMessageText(
            mes['chat_id'], mes['id'], f"```\n{asts.format_help()}\n```",
            TextParseMode.MarkDown)
    else:
        try:
            if not robot._logined:
                raise ValueError('bot_token is not set. This future need a bot. Please contact @BotFather to get a valid bot_token.')  # noqa: E501
            r = asts.parse_intermixed_args(argv[1:])
            if r.add_suffix and r.name:
                un = await robot.getUsername()
                if not r.name.endswith(f'_by_{un}'):
                    r.name += f'_by_{un}'
                validate_sticker_set_name(r.name)
            if r.id is None and r.name is None:
                raise ValueError('name or ID is needed.')
            if mes['reply_to_message_id'] == 0:
                raise ValueError('Reply a sticker message is needed.')
            nmes = await lib.getMessage(mes['reply_in_chat_id'],
                                        mes['reply_to_message_id'])
            if nmes is None:
                raise ValueError('Can not get the replied message.')
            if nmes['content']['@type'] != 'messageSticker':
                raise ValueError('Reply a sticker message is needed.')
            width = nmes['content']['sticker']['width']
            height = nmes['content']['sticker']['height']
            if max(width, height) != 512:
                raise ValueError('Invalid width or height')
            fid = nmes['content']['sticker']['sticker']['remote']['id']
            emoji = nmes['content']['sticker']['emoji'] if r.emoji is None else r.emoji  # noqa: E501
            if fid == '':
                raise ValueError("The target sticker's file id is empty.")
            st = {"@type": "inputStickerStatic", "sticker": {"@type": "inputFileRemote", "id": fid}, "emojis": emoji}  # noqa: E501
            if r.name is None:
                si = await lib.getStickerSet(r.id)
                if si is None:
                    raise ValueError('Can not get sticker set from ID.')
                r.name = si['name']
            uid = await lib.getUid()
            if uid is None:
                raise ValueError('Can not get user ID.')
            re = await robot.addStickerToSet(uid, r.name, st)
            if re is None:
                raise ValueError('Failed to add sticker to set')
            if r.delete:
                re = await lib.deleteMessages(mes['chat_id'], mes['id'])
            else:
                re = await lib.editMessageText(mes['chat_id'], mes['id'], "Added sticker to set successfully.")  # noqa: E501
        except ValueError as e:
            if len(e.args) == 0:
                re = await lib.editMessageText(mes['chat_id'], mes['id'], "Unknown error.")  # noqa: E501
            else:
                re = await lib.editMessageText(mes['chat_id'], mes['id'], f"```\n{asts.format_usage()}{asts.prog}: error: {e.args[0] if len(e.args) == 1 else e.args}\n```", TextParseMode.MarkDown)  # noqa: E501
        except Exception:
            re = await lib.editMessageText(mes['chat_id'], mes['id'], f"```\n{format_exc()}\n```", TextParseMode.MarkDown)  # noqa: E501
    if re is None or re is False:
        print('Can not edit/delete message.')


async def get_chat_id_from_name(lib: TdLib, name: str) -> int:
    re = await lib.searchChatsOnServer(name)
    if re is None:
        raise ValueError('Can not search chats.')
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
        raise ValueError('Multipled chats returned, please speicfy a better name.')  # noqa: E501


async def handle_delete_all_my_messages(lib: TdLib, mes: dict,
                                        argv: List[str]):
    if len(argv) == 1:
        re = await lib.editMessageText(
            mes['chat_id'], mes['id'], f"```\n{damm.format_help()}\n```",
            TextParseMode.MarkDown)
    else:
        try:
            r = damm.parse_intermixed_args(argv[1:])
            if r.chat_id is None and r.chat_name is None:
                r.chat_id = mes['chat_id']
            cid = await get_chat_id_from_name(lib, r.chat_name) if r.chat_id is None else r.chat_id  # noqa: E501
            text = 'all the time'
            if r.start_time is not None and r.end_time is not None:
                text = f"between `{timeToStr(r.start_time)}` and `{timeToStr(r.end_time)}`"  # noqa: E501
            elif r.start_time is not None:
                text = f"after `{timeToStr(r.start_time)}`"
            elif r.end_time is not None:
                text = f"before `{timeToStr(r.end_time)}`"
            re = await lib.editMessageText(mes['chat_id'], mes['id'], f"Started delete messages {text}.", TextParseMode.MarkDown)  # noqa: E501
            re = await lib.deleteAllMyMessageInChat(cid, r.start_time, r.end_time, False, [mes['id']])  # noqa: E501
            if re is None:
                raise ValueError('Failed to delete.')
            re = await lib.editMessageText(mes['chat_id'], mes['id'], f"Deleted `{re}` messages {text}.", TextParseMode.MarkDown)  # noqa: E501
        except ValueError as e:
            if len(e.args) == 0:
                re = await lib.editMessageText(mes['chat_id'], mes['id'], "Unknown error.")  # noqa: E501
            else:
                re = await lib.editMessageText(mes['chat_id'], mes['id'], f"```\n{damm.format_usage()}{damm.prog}: error: {e.args[0] if len(e.args) == 1 else e.args}\n```", TextParseMode.MarkDown)  # noqa: E501
        except Exception:
            re = await lib.editMessageText(mes['chat_id'], mes['id'], f"```\n{format_exc()}\n```", TextParseMode.MarkDown)  # noqa: E501
    if re is None:
        print('Can not edit message.')


async def handle_nbnhhsh(lib: TdLib, mes: dict, argv: List[str]):
    if len(argv) == 1:
        re = await lib.editMessageText(
            mes['chat_id'], mes['id'], f"```\n{nbnhhsh.format_help()}\n```",
            TextParseMode.MarkDown)
    else:
        try:
            opt = nbnhhsh.parse_intermixed_args(argv[1:])
            re = requests.post("https://lab.magiconch.com/api/nbnhhsh/guess", {"text": opt.缩写}, timeout=opt.timeout)  # noqa: E501
            if re.status_code >= 400:
                raise ValueError(f'{re.status_code} {re.reason}\n{re.text}')
            re = re.json()
            tl = []
            for kw in re:
                text = f"`{kw['name']}`: "
                if 'trans' in kw and isinstance(kw['trans'], list):
                    text += ', '.join(kw['trans'])
                else:
                    text += '未找到结果'
                tl.append(text)
            text = '\n'.join(tl)
            if text == '':
                text = '没有结果'
            re = await lib.editMessageText(mes['chat_id'], mes['id'], text, TextParseMode.MarkDown)  # noqa: E501
        except ValueError as e:
            if len(e.args) == 0:
                re = await lib.editMessageText(mes['chat_id'], mes['id'], "Unknown error.")  # noqa: E501
            else:
                re = await lib.editMessageText(mes['chat_id'], mes['id'], f"```\n{nbnhhsh.format_usage()}{nbnhhsh.prog}: error: {e.args[0] if len(e.args) == 1 else e.args}\n```", TextParseMode.MarkDown)  # noqa: E501
        except requests.Timeout:
            re = await lib.editMessageText(mes['chat_id'], mes['id'], "查询超时")
        except Exception:
            re = await lib.editMessageText(mes['chat_id'], mes['id'], f"```\n{format_exc()}\n```", TextParseMode.MarkDown)  # noqa: E501
    if re is None:
        print('Can not edit message.')


async def handle_search_message(lib: TdLib, mes: dict, argv: List[str]):
    if len(argv) == 1:
        re = await lib.editMessageText(
            mes['chat_id'], mes['id'], f"```\n{sm.format_help()}\n```",
            TextParseMode.MarkDown)
    else:
        try:
            opt = sm.parse_intermixed_args(argv[1:])
            chat_id = opt.chat_id if opt.chat_id else mes['chat_id']
            await lib.editMessageText(mes['chat_id'], mes['id'], f'Started to search `{opt.keyword}`.', TextParseMode.MarkDown)  # noqa: E501
            mess: List[int] = []
            tmes = 0
            st: int = None
            et: int = None
            fmi: int = None
            n = time()
            while True:
                mesl = await lib.searchChatMessages(chat_id, from_message_id=fmi, limit=100)  # noqa: 
                if mesl is None or len(mesl['messages']) == 0:
                    break
                fmi = mesl['messages'][-1]['id']
                for nmes in mesl['messages']:
                    if nmes['content']['@type'] != 'messageText':
                        continue
                    if nmes['id'] == mes['id']:
                        continue
                    tmes += 1
                    if st is None or st > nmes['date']:
                        st = nmes['date']
                    if et is None or et < nmes['date']:
                        et = nmes['date']
                    text: str = nmes['content']['text']['text']
                    if text.find(opt.keyword) > -1:
                        mess.append(nmes['id'])
                if (opt.max_searched > -1 and tmes >= opt.max_searched) or len(mess) >= 20:  # noqa: E501
                    break
                if n + 10 < time():
                    await lib.editMessageText(mes['chat_id'], mes['id'], f'Search `{opt.keyword}`...\nAlready searched `{tmes}` messages, founded `{len(mess)}` result.', TextParseMode.MarkDown)  # noqa: E501
                    n = time()
            tmp = '' if tmes == 0 else f" (from <code>{timeToStr(st)}</code> to <code>{timeToStr(et)}</code>)"  # noqa: E501
            r = f"Searched <code>{escape(opt.keyword)}</code> in <code>{tmes}</code> messages{tmp}, founded <code>{len(mess)}</code> results:"  # noqa: E501
            for i in mess:
                link = await lib.getMessageLink(chat_id, i)
                if link is None:
                    r += "\nFailed to get message link."
                else:
                    r += f"\n{escape(link['link'])}"
            re = await lib.editMessageText(mes['chat_id'], mes['id'], r, TextParseMode.HTML)  # noqa: E501
        except ValueError as e:
            if len(e.args) == 0:
                re = await lib.editMessageText(mes['chat_id'], mes['id'], "Unknown error.")  # noqa: E501
            else:
                re = await lib.editMessageText(mes['chat_id'], mes['id'], f"```\n{sm.format_usage()}{sm.prog}: error: {e.args[0] if len(e.args) == 1 else e.args}\n```", TextParseMode.MarkDown)  # noqa: E501
        except Exception:
            re = await lib.editMessageText(mes['chat_id'], mes['id'], f"```\n{format_exc()}\n```", TextParseMode.MarkDown)  # noqa: E501
    if re is None:
        print('Can not edit message.')


async def handle_optimize_storage(lib: TdLib, robot: TdLib, mes: dict,
                                  argv: List[str]):
    try:
        opt = om.parse_intermixed_args(argv[1:])
        if opt.help:
            re = await lib.editMessageText(
                mes['chat_id'], mes['id'], f"```\n{om.format_help()}\n```",
                TextParseMode.MarkDown)
        else:
            if opt.robot and not robot._logined:
                raise ValueError('Robot is not logined.')
            d = {'return_deleted_file_statistics': opt.return_deleted_file_statistics}  # noqa: E501
            if opt.size:
                d['size'] = opt.size
            if opt.ttl:
                d['ttl'] = opt.ttl
            if opt.count:
                d['count'] = opt.count
            if opt.immunity_delay:
                d['immunity_delay'] = opt.immunity_delay
            if opt.chat_ids:
                d['chat_ids'] = opt.chat_ids
            if opt.exclude_chat_ids:
                d['exclude_chat_ids'] = opt.exclude_chat_ids
            if opt.chat_limit:
                d['chat_limit'] = opt.chat_limit
            r = await robot.optimizeStorage(**d) if opt.robot else await lib.optimizeStorage(**d)  # noqa: E501
            if r is None:
                raise ValueError('Failed to optimize the storage.')
            text = f"Optimized successfully.\nTotal file size: <code>{r['size']}B</code>\nFile count: <code>{r['count']}</code>"  # noqa: E501
            re = await lib.editMessageText(mes['chat_id'], mes['id'], text, TextParseMode.HTML)  # noqa: E501
    except ValueError as e:
        if len(e.args) == 0:
            re = await lib.editMessageText(mes['chat_id'], mes['id'], "Unknown error.")  # noqa: E501
        else:
            re = await lib.editMessageText(mes['chat_id'], mes['id'], f"```\n{om.format_usage()}{om.prog}: error: {e.args[0] if len(e.args) == 1 else e.args}\n```", TextParseMode.MarkDown)  # noqa: E501
    except Exception:
        re = await lib.editMessageText(mes['chat_id'], mes['id'], f"```\n{format_exc()}\n```", TextParseMode.MarkDown)  # noqa: E501
    if re is None:
        print('Can not edit message.')


async def main(lib: TdLib, robot: TdLib):
    with open('tdlib.json', 'r', encoding='UTF-8') as f:
        se = load(f)
    if not await lib.login(se['TdlibParameters'], se['encryption_key'],
                           se.get("proxy"), se.get("phone_number")):
        raise ValueError('Can not login')
    if se.get("bot_token") is not None:
        paras = se['TdlibParameters'].copy()
        if se.get("BotTdlibParameters"):
            paras.update(se["BotTdlibParameters"])
        ek = se['bot_encryption_key'] if se.get("bot_encryption_key") else se['encryption_key']  # noqa: E501
        if not await robot.login(paras, ek, se.get("proxy"), bot_token=se["bot_token"]):  # noqa: E501
            raise ValueError('Can not login as bot')
    uid = await lib.getUid()
    while True:
        mes = await lib.receive('updateNewMessage')
        if mes['@type'] == 'updateNewMessage':
            mes = mes['message']
            if mes['sender_id']['@type'] != 'messageSenderUser':
                continue
            if mes['sender_id']['user_id'] != uid:
                continue
            if mes['content']['@type'] != 'messageText':
                continue

            def err(e):
                e = e.result()
                if e is None:
                    print('Can not edit message.')
            text: str = mes['content']['text']['text']
            text = text.lstrip("(NOFWD)")
            text = text.lstrip("(NOQQ)")
            if text == '-hello':
                re = lib.editMessageText(mes['chat_id'], mes['id'],
                                         'Hello World!')
                asyncio.create_task(re).add_done_callback(err)
            elif text in ['-msginfo', '-messageinfo']:  # noqa: E501
                re = handle_message_info(lib, mes)
                asyncio.create_task(re)
            elif text.startswith('-'):
                argv = commandLineToArgv(text)
                if argv[0] in ['-createnewstickerset', '-cnss']:
                    re = handle_create_new_sticker_set(lib, robot, mes, argv)
                    asyncio.create_task(re)
                elif argv[0] in ['-addstickertoset', '-asts']:
                    re = handle_add_sticker_to_set(lib, robot, mes, argv)
                    asyncio.create_task(re)
                elif argv[0] in ['-deleteallmymessages', '-damm']:
                    re = handle_delete_all_my_messages(lib, mes, argv)
                    asyncio.create_task(re)
                elif argv[0] == '-nbnhhsh':
                    asyncio.create_task(handle_nbnhhsh(lib, mes, argv))
                elif argv[0] in ['-searchmessage', '-sm']:
                    asyncio.create_task(handle_search_message(lib, mes, argv))
                elif argv[0] in ['-optimizestorage', '-om']:
                    asyncio.create_task(handle_optimize_storage(lib, robot, mes, argv))  # noqa: E501


with TdLib() as lib:
    with TdLib() as robot:
        asyncio.run(main(lib, robot))
