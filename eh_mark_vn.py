from argparse import ArgumentParser
from ehapi import EHC
from sys import exit
from re import compile


# きゃべつそふと BGI
CABBAGE_SOFT_BGI = compile(r'^(tmb_|ex_|br_)?([ehm]v|bg)\d+[a-z_0-9A-Z]*\.(jpg|png)$')  # noqa: E501
# きゃべつそふと 星恋＊ティンクル
HOSHIKOI_TWINKLE = compile(r'^(((ev|z_)?etc|nagi|saku|sd|sora|tama)\d+)[a-z_]*(_large)?\.(jpg|png)$')  # noqa: E501
HOSHIKOI_H_LIST = ['etc06', 'nagi08', 'nagi09', 'nagi10', 'nagi11', 'nagi12', 'nagi13', 'nagi14', 'nagi15', 'nagi16', 'nagi17', 'nagi19', 'nagi22', 'saku02', 'saku03', 'saku08', 'saku09', 'saku11', 'saku12', 'saku13', 'saku14', 'saku15', 'saku16', 'saku17', 'saku18', 'sora01', 'sora02', 'sora03', 'sora05', 'sora07', 'sora09', 'sora10', 'sora11', 'sora12', 'sora13', 'sora14', 'sora15', 'sora16', 'sora17', 'sora18', 'sora19', 'sora21', 'tama03', 'tama08', 'tama09', 'tama10', 'tama11', 'tama12', 'tama13', 'tama16', 'tama17', 'tama18', 'tama19', 'z_etc28']  # noqa: E501
# Lump of Sugar
LOS_BGI = compile(r'^h?ev(sd)?h?_.*\.(png|jpg)')
# Lump of Sugar ねこツク、さくら。
LOS_BGI_H = compile(r'^ev_[a-z]h.*\.(png|jpg)')
p = ArgumentParser()
p.add_argument('-b', '--base', default='http://localhost:8080', help='API Host')  # noqa: E501
p.add_argument('-t', '--token', help='Token')
p.add_argument('-p', '--print', action='store_true', default=False, help='Print page')  # noqa: E501
p.add_argument('-d', '--dryrun', action='store_true', default=False, help='Dry run')  # noqa: E501
p.add_argument('gid', help='Gallery id', type=int)
p.add_argument('typ', nargs='?', default='auto', choices=['auto', 'cabbage-soft', 'cabbage-soft/hoshikoi-twinkle'], help='Type')  # noqa: E501
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


def check_tag(tags: list, tag: str):
    for t in tags:
        if t['tag'] == tag:
            return True
    return False


def check_cabbage_soft_pages(pages):
    for p in pages:
        name: str = p['name']
        if name.startswith("tmb_"):
            name = name[4:]
            is_nsfw = name.startswith("hv")
            mark(p, changes, is_nsfw, True)
        else:
            if name.startswith("ex_") or name.startswith('br_'):
                name = name[3:]
            if name.startswith("hv"):
                mark(p, changes, True, False)
            else:
                mark(p, changes, False, False)


def check_hoshikoi_twinkle(pages):
    for p in pages:
        name: str = p['name']
        m = HOSHIKOI_TWINKLE.match(name)
        if not m:
            continue
        t = m.group(1)
        if t in HOSHIKOI_H_LIST:
            mark(p, changes, True, False)
        else:
            mark(p, changes, False, False)


def guess_cabbage_soft(pages):
    c = 0
    for p in pages:
        name: str = p['name']
        if name.startswith('_') or CABBAGE_SOFT_BGI.match(name):
            c += 1
    return c / len(pages)


def guess_hoshikoi_twinkle(pages):
    c = 0
    for p in pages:
        name: str = p['name']
        if name.startswith('_') or HOSHIKOI_TWINKLE.match(name):
            c += 1
        else:
            print(name)
    return c / len(pages)


def guess_engine(pages, tags):
    if check_tag(tags, 'group:cabbage soft'):
        cabbage_soft = guess_cabbage_soft(pages)
        print("きゃべつそふと(BGI) coverage:", cabbage_soft)
        if cabbage_soft >= 0.9:
            return 'cabbage-soft'
        hoshikoi = guess_hoshikoi_twinkle(pages)
        print("星恋＊ティンクル coverage:", hoshikoi)
        if hoshikoi >= 0.9:
            return 'cabbage-soft/hoshikoi-twinkle'
    return None


with EHC() as c:
    c.base = f"{arg.base}/api"
    if arg.token:
        c.ses.headers.update({'X-TOKEN': arg.token})
    gallery = c.get_gallery(arg.gid)
    pages = gallery['pages']
    tags = gallery['tags']
    if arg.print:
        for p in pages:
            print(p)
        exit(0)
    typ = arg.typ
    if typ == 'auto':
        typ = guess_engine(pages, tags)
    if not typ:
        raise ValueError('Unknown engine.')
    changes = []
    if typ == 'cabbage-soft':
        check_cabbage_soft_pages(pages)
    elif typ == 'cabbage-soft/hoshikoi-twinkle':
        check_hoshikoi_twinkle(pages)
    if arg.dryrun:
        exit(0)
    c.update_file_meta_json(changes)
