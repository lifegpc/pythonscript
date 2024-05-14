import _rssbotlib
from argparse import ArgumentParser
import re
from typing import List
from os.path import join, splitext, isdir, exists, split
from os import listdir, remove, link, symlink, makedirs
from subprocess import PIPE, Popen


FMT = re.compile(r"(\d+)(/(\d+))?")


def generate_thumb(input: str, output: str):
    p = Popen([arg.ffmpeg, '-i', input, '-c', 'copy',
              '-y', output], stdout=PIPE, stderr=PIPE)
    p.wait()
    if p.returncode != 0:
        print(p.stdout.read().decode(errors='ignore'))
        print(p.stderr.read().decode(errors='ignore'))
        raise ValueError(f"Failed to generate thumbnail for {input}")


def generate_path(input: str):
    ext = splitext(input)[1]
    i = _rssbotlib.VideoInfo()
    if not i.parse(input):
        raise ValueError(f"Failed to parse {input}")
    s = i.streams
    thumb = False
    for stream in s:
        if stream.is_video:
            thumb = True
            break
    m = i.meta.to_dict()
    tmp = {}
    for i in m:
        tmp[i.lower()] = m[i]
    m = tmp
    artist = m.get('album_artist', m.get('artist', None))
    album = m.get('album', None)
    title = m.get('title', None)
    disc = m.get('disc', '1/1')
    track = m.get('track', None)
    if artist is None or album is None or title is None:
        raise ValueError("No artist, album or title")
    thumb = join(arg.OUTPUT, artist, album, arg.cover) if thumb else None
    discs = FMT.match(disc)
    if discs is None:
        raise ValueError(f"Failed to parse discs {disc}")
    discs = discs.group(1, 3)
    discs = (int(discs[0]), int(discs[1]) if discs[1] is not None else None)
    if discs[1] == 1 or discs[1] is None:
        if track is None:
            return (join(arg.OUTPUT, artist, album, title + ext), thumb)
        else:
            tracks = FMT.match(track)
            if tracks is None:
                raise ValueError(f"Failed to parse tracks {track}")
            tracks = tracks.group(1, 3)
            track0 = int(tracks[0])
            return (join(arg.OUTPUT, artist, album,
                         f"{track0:02} - {title}{ext}"), thumb)
    else:
        if track is None:
            return (join(arg.OUTPUT, artist, album, f"Disc {discs[0]}",
                         f"{title}{ext}"), thumb)
        else:
            tracks = FMT.match(track)
            if tracks is None:
                raise ValueError(f"Failed to parse tracks {track}")
            tracks = tracks.group(1, 3)
            track0 = int(tracks[0])
            return (join(arg.OUTPUT, artist, album, f"Disc {discs[0]}",
                         f"{track0:02} - {title}{ext}"), thumb)


def get_m4a_files(dir: str, r: bool) -> List[str]:
    if not isdir(dir):
        return []
    files = listdir(dir)
    re = []
    for file in files:
        file = join(dir, file)
        if isdir(file):
            if r:
                re += get_m4a_files(file, r)
        elif file.endswith('.m4a') or file.endswith(".flac") or file.endswith(".mp3"):
            re.append(file)
    return re


p = ArgumentParser()
p.add_argument("INPUT", help="Input directory")
p.add_argument("OUTPUT", help="Output directory")
p.add_argument("-F", "--ffmpeg", help="Path to ffmpeg", default="ffmpeg")
p.add_argument("-v", "--verbose", help="Verbose output",
               action="store_true", default=False)
p.add_argument("-f", "--force", help="Overwrite existing files",
               action="store_true", default=False)
p.add_argument("-r", "--recursive", help="Recursive search",
               action="store_true", default=False)
p.add_argument("-c", "--cover", help="Cover file name", default="cover.jpg")
p.add_argument("-H", "--hardlink", help="Use hard link instead of copy",
               action="store_true", default=False)
p.add_argument("-d", "--delete", help="Delete output", action="store_true",
               default=False)
arg = p.parse_intermixed_args()
print(arg)
for f in get_m4a_files(arg.INPUT, arg.recursive):
    if arg.verbose:
        print(f"Processing {f}")
    r = generate_path(f)
    if arg.verbose:
        print(f"Target path: {r[0]}")
    if r[1]:
        thumb = r[1]
        if arg.verbose:
            print(f"Target thumb: {thumb}")
        if arg.delete and exists(thumb):
            remove(thumb)
        elif not exists(thumb):
            makedirs(split(thumb)[0], exist_ok=True)
            generate_thumb(f, thumb)
    if exists(r[0]):
        if arg.delete:
            remove(r[0])
            if arg.verbose:
                print(f"File {r[0]} deleted.")
            continue
        if not arg.force:
            print(f"File {r[0]} exists, skipped")
            continue
    if exists(r[0]):
        remove(r[0])
    makedirs(split(r[0])[0], exist_ok=True)
    if arg.hardlink:
        link(f, r[0])
    else:
        symlink(f, r[0])
    if arg.verbose:
        print(f"Linked {f} to {r[0]}")
