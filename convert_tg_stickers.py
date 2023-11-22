import _rssbotlib
from argparse import ArgumentParser
from os import listdir
from os.path import exists, isdir, join
from subprocess import PIPE, Popen
from typing import List


def get_source_size(src) -> (int, int):
    f = _rssbotlib.VideoInfo()
    if not f.parse(src):
        raise ValueError(f"Failed to parse {src}")
    s = f.streams
    for i in s:
        if i.is_video:
            return i.width, i.height
    raise ValueError(f"Failed to find video stream in {src}")


def get_png_files(dir: str, r: bool) -> List[str]:
    if not isdir(dir):
        return []
    files = listdir(dir)
    re = []
    for file in files:
        file = join(dir, file)
        if isdir(file):
            if r:
                re += get_png_files(file, r)
        elif file.endswith('.png') and not file.endswith(f'{arg.suffix}.png'):
            re.append(file)
    return re


def convert_png(src: str, dest: str, w: int, h: int):
    p = Popen([arg.ffmpeg, '-i', src, '-vf', f'scale={w}x{h}', "-y", dest],
              stdout=PIPE, stderr=PIPE)
    p.wait()
    if p.returncode != 0:
        print(p.stdout.read().decode(errors='ignore'))
        print(p.stderr.read().decode(errors='ignore'))
        raise ValueError(f"Failed to convert {src} to {dest}")
    if arg.verbose:
        print(f"Converted {src} to {dest}")


p = ArgumentParser()
p.add_argument("-m", "--max-length", help="Maximum length of the sticker",
               type=int, default=512)
p.add_argument("-r", "--recursive", help="Recursive search",
               action="store_true", default=False)
p.add_argument("-s", "--suffix", help="Suffix of the output sticker",
               default="_tg")
p.add_argument('-f', '--force', action='store_true', default=False,
               help='Overwrite existing files')
p.add_argument('-v', '--verbose', action='store_true', default=False,
               help='Verbose output')
p.add_argument('-F', '--ffmpeg', help='Path to ffmpeg', default='ffmpeg')
p.add_argument("DIR", help="Directory of the stickers", nargs="+")
arg = p.parse_intermixed_args()
print(arg)
for d in arg.DIR:
    for f in get_png_files(d, arg.recursive):
        if arg.verbose:
            print(f"Processing {f}")
        w, h = get_source_size(f)
        if arg.verbose:
            print(f"Source size: {w}x{h}")
        if w > h:
            h = round(arg.max_length * h / w)
            w = arg.max_length
        else:
            w = round(arg.max_length * w / h)
            h = arg.max_length
        if arg.verbose:
            print(f"Target size: {w}x{h}")
        target = f[:-4] + arg.suffix + '.png'
        if exists(target) and not arg.force:
            if arg.verbose:
                print(f"Skip {target}")
            continue
        convert_png(f, target, w, h)
