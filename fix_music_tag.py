from argparse import ArgumentParser
from os import listdir
from os.path import isdir, isfile, join
import re
from typing import List
import taglib


ARTIST_SEP = re.compile(r'(/|&|;)')


def get_files(dir: str, r: bool) -> List[str]:
    if isfile(dir):
        return [dir]
    if not isdir(dir):
        return []
    files = listdir(dir)
    re = []
    for file in files:
        file = join(dir, file)
        if isdir(file):
            if r:
                re += get_files(file, r)
        elif file.endswith('.m4a') or file.endswith(".flac") or file.endswith(".mp3"):  # noqa: E501
            re.append(file)
    return re


def fix_tag(file: str, verbose: bool):
    f = taglib.File(file)
    need_save = False

    def change(tag, value):
        nonlocal need_save
        if not need_save:
            need_save = True
            print('Change file tag:', file)
        print(tag, f.tags[tag], '->', value)
        f.tags[tag] = value

    try:
        if verbose:
            print(file)
        for tag in f.tags:
            value = f.tags[tag]
            if tag in ['ARTIST', 'ALBUMARTIST']:
                result = []
                need_change = False
                for artist in value:
                    r = ARTIST_SEP.split(artist)
                    if len(r) > 1:
                        need_change = True
                    for a in r:
                        ar = a.strip()
                        if ar in ['&', '/', ';']:
                            continue
                        result.append(ar)
                if need_change:
                    change(tag, result)
                elif verbose:
                    print(tag, f.tags[tag])
        if need_save:
            f.save()
    finally:
        f.close()


p = ArgumentParser()
p.add_argument("INPUT", help="Input directory")
p.add_argument("-r", "--recursive", help="Recursive search",
               action="store_true", default=False)
p.add_argument("-v", "--verbose", help="verbose output",
               action="store_true", default=False)
arg = p.parse_intermixed_args()
for f in get_files(arg.INPUT, arg.recursive):
    fix_tag(f, arg.verbose)
