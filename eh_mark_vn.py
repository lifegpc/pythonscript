from argparse import ArgumentParser
from ehapi import EHC
from sys import exit
from re import compile


BGI = compile(r'^(tmb_)?([ehm]v\d+[a-z_]?|scene\d+)\.(jpg|png)$')
p = ArgumentParser()
p.add_argument('-b', '--base', default='http://localhost:8080', help='API Host')  # noqa: E501
p.add_argument('-t', '--token', help='Token')
p.add_argument('-p', '--print', action='store_true', default=False, help='Print page')  # noqa: E501
p.add_argument('-d', '--dryrun', action='store_true', default=False, help='Dry run')  # noqa: E501
p.add_argument('gid', help='Gallery id', type=int)
p.add_argument('typ', nargs='?', default='auto', choices=['auto', 'bgi'], help='Engine')  # noqa: E501
arg = p.parse_intermixed_args()


def mark(page, changes, is_nsfw=None, is_ad=None):
    token = page['token']
    index = page['index']
    name = page['name']
    width = page['width']
    height = page['height']
    t = []
    if is_nsfw is not None and page['is_nsfw'] != is_nsfw:
        t.append('NSFW' if is_nsfw else 'SFW')
    if is_ad is not None and page['is_ad'] != is_ad:
        t.append('AD' if is_ad else 'non-AD')
    if not len(t):
        return
    changes.append({"token": token, 'is_ad': is_ad, 'is_nsfw': is_nsfw})
    print(f'Mark {index}.{name}({width}x{height}) as {", ".join(t)}')


def bgi_check_pages(pages, changes):
    for p in pages:
        name: str = p['name']
        if name.startswith("tmb_"):
            name = name[4:]
            is_nsfw = name.startswith("hv") or name.startswith("scene")
            mark(p, changes, is_nsfw, True)
        elif name.startswith("hv"):
            mark(p, changes, True, False)
        else:
            mark(p, changes, False, False)


def guess_as_bgi(pages):
    c = 0
    for p in pages:
        name: str = p['name']
        if name.startswith('_') or BGI.match(name):
            c += 1
    return c / len(pages)


def guess_engine(pages):
    bgi = guess_as_bgi(pages)
    print('BGI coverage:', bgi)
    if bgi >= 0.9:
        return 'bgi'
    return None


with EHC() as c:
    c.base = f"{arg.base}/api"
    if arg.token:
        c.ses.headers.update({'X-TOKEN': arg.token})
    gallery = c.get_gallery(arg.gid)
    pages = gallery['pages']
    if arg.print:
        for p in pages:
            print(p)
        exit(0)
    typ = arg.typ
    if typ == 'auto':
        typ = guess_engine(pages)
    if not typ:
        raise ValueError('Unknown engine.')
    changes = []
    if typ == 'bgi':
        bgi_check_pages(pages, changes)
    if arg.dryrun:
        exit(0)
    c.update_file_meta_json(changes)
