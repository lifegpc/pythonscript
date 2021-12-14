from argparse import ArgumentParser
import asyncio
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
from util import commandLineToArgv, timeToStr


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
cnss.add_argument('name', help="Sticker set name. Can contain only English letters, digits and underscores. 1-64 characters", type=validate_sticker_set_name)  # noqa: E501
cnss.add_argument('title', help="Sticker set title. 1-64 characters", type=validate_sticker_set_title)  # noqa: E501
cnss.add_argument('source', help='Source of the sticker set', nargs='?', default='')  # noqa: E501
cnss.add_argument('-e', '--emoji', help='Emojis corresponding to the sticker', metavar='EMOJI', dest='emoji')  # noqa: E501


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


async def handle_create_new_sticker_set(lib: TdLib, mes: dict,
                                        argv: List[str]):
    if len(argv) == 1:
        re = await lib.editMessageText(
            mes['chat_id'], mes['id'], f"```\n{cnss.format_help()}\n```",
            TextParseMode.MarkDown)
    else:
        try:
            r = cnss.parse_intermixed_args(argv[1:])
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
            st = [{"@type": "inputStickerStatic", "sticker": {"@type": "inputFileRemote", "id": fid}, "emojis": emoji}]  # noqa: E501
            r = await lib.createNewStickerSet(r.title, r.name, st, source=r.source)  # noqa: E501
            if r is None:
                raise ValueError('Can not create new sticker set.')
            re = await lib.editMessageText(mes['chat_id'], mes['id'], f"Created successfully.\nSticker Set ID: {r['id']}\nhttps://t.me/addstickers/{r['name']}")  # noqa: E501
        except ValueError as e:
            if len(e.args) == 0:
                re = await lib.editMessageText(mes['chat_id'], mes['id'], "Unknown error.")  # noqa: E501
            else:
                re = await lib.editMessageText(mes['chat_id'], mes['id'], f"```\n{cnss.format_usage()}\n{cnss.prog}: error: {e.args[0] if len(e.args) == 1 else e.args}\n```", TextParseMode.MarkDown)  # noqa: E501
        except Exception:
            re = await lib.editMessageText(mes['chat_id'], mes['id'], f"```\n{format_exc()}\n```", TextParseMode.MarkDown)  # noqa: E501
    if re is None:
        print('Can not edit message')


async def main(lib: TdLib):
    with open('tdlib.json', 'r', encoding='UTF-8') as f:
        se = load(f)
    if not await lib.login(se['TdlibParameters'], se['encryption_key'],
                           se.get("proxy"), se.get("phone_number")):
        raise ValueError('Can not login')
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
                print(e)
            if mes['content']['text']['text'] == '-hello':
                re = lib.editMessageText(mes['chat_id'], mes['id'],
                                         'Hello World!')
                asyncio.create_task(re).add_done_callback(err)
            elif mes['content']['text']['text'] in ['-msginfo', '-messageinfo']:  # noqa: E501
                re = handle_message_info(lib, mes)
                asyncio.create_task(re)
            elif mes['content']['text']['text'].startswith('-'):
                argv = commandLineToArgv(mes['content']['text']['text'])
                if argv[0] in ['-createnewstickerset', '-cnss']:
                    re = handle_create_new_sticker_set(lib, mes, argv)
                    asyncio.create_task(re)


with TdLib(True) as lib:
    asyncio.run(main(lib))
