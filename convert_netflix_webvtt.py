from argparse import ArgumentParser
from os import listdir
from os.path import isdir, join, exists
from typing import List
import webvtt


def get_vtt_files(dir: str, r: bool) -> List[str]:
    if not isdir(dir):
        return []
    files = listdir(dir)
    re = []
    for file in files:
        file = join(dir, file)
        if isdir(file):
            if r:
                re += get_vtt_files(file, r)
        elif file.endswith('.vtt'):
            re.append(file)
    return re


p = ArgumentParser(description='Convert Netflix WebVTT to SRT')
p.add_argument('input', help='Input directory', nargs='+')
p.add_argument('-r', '--recursive', action='store_true', default=False,
               help='Recursively process input directory')
p.add_argument('-f', '--force', action='store_true', default=False,
               help='Overwrite existing files')
p.add_argument('-v', '--verbose', action='store_true', default=False,
               help='Verbose output')
arg = p.parse_intermixed_args()
for dir in arg.input:
    for file in get_vtt_files(dir, arg.recursive):
        srt = file[:-3] + 'srt'
        if exists(srt) and not arg.force:
            if arg.verbose:
                print(f"Skip {file}")
            continue
        vtt = webvtt.read(file)
        for i in vtt:
            i.text = i.text
        vtt.save_as_srt(srt)
        if arg.verbose:
            print(f"Converted {file} to {srt}")
