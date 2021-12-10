from getopt import gnu_getopt as getopt, GetoptError
from os.path import basename, dirname, join, splitext
from re import compile, search
from sys import argv, exit
from typing import List, Optional
try:
    from _rssbotlib import AVDict, version, VideoInfo
    have_rssbotlib = True
except ImportError:
    have_rssbotlib = False


RSSBOTLIB_NOTFOUND = '''rssbotlib not found.
The source code is available at https://github.com/lifegpc/ffmpeg-study/tree/master/rssbotlib'''  # noqa: E501
DUR_REG = compile(r'^(?P<sign>[\+-])?(((?P<h>\d+):)?((?P<min>\d+):))?(?P<sec>\d+)(\.(?P<ms>\d+))?$')  # noqa: E501


def prase_duration(s: str) -> float:
    r = search(DUR_REG, s)
    if r is None:
        raise ValueError(f'Can not parse duration "{s}"')
    rd = r.groupdict()
    t = int(rd['sec'])
    if rd['ms']:
        t += int(rd['ms']) / (10 ** len(rd['ms']))
    if rd['min']:
        t += int(rd['min']) * 60
    if rd['h']:
        t += int(rd['h']) * 3600
    if rd['sign'] == '-':
        t = -t
    return t


def generate_good_filename(meta: AVDict) -> Optional[str]:
    m = meta.to_dict()
    if 'title' in m and 'artist' in m:
        return f"{m['artist']} - {m['title']}.lrc"
    elif 'title' in m:
        return f"{m['title']}.lrc"


class Cml:
    def __init__(self, arg: List[str]) -> None:
        self.output = None
        self.file = None
        self.verbose = False
        self.duration = None
        self.dir = None
        if len(arg) == 0:
            self.print_help()
            exit(0)
        try:
            r = getopt(arg, '-hVvo:f:t:d:',
                       ['help', 'version', 'verbose', 'output=', 'file=',
                        'duration=', 'dir='])
            for i in r[0]:
                if i[0] == '-h' or i[0] == '--help':
                    self.print_help()
                    exit(0)
                elif i[0] == '-V' or i[0] == '--version':
                    self.print_version()
                    exit(0)
                elif i[0] == '-v' or i[0] == '--verbose':
                    self.verbose = True
                elif i[0] == '-o' or i[0] == '--output':
                    self.output = i[1]
                elif i[0] == '-f' or i[0] == '--file':
                    self.file = i[1]
                elif i[0] == '-t' or i[0] == '--duration':
                    self.duration = prase_duration(i[1])
                elif i[0] == '-d' or i[0] == '--dir':
                    self.dir = i[1]
            if len(r[1]) == 0:
                raise GetoptError('Input lyric file is needed.')
            if len(r[1]) > 1:
                raise GetoptError('Too much input lyric file.')
            self.input = r[1][0]
        except GetoptError as e:
            print(e.msg)
            exit(1)

    def print_help(self):
        print('''convert_lrc.py [options] <lyric file>
Convert translated lryics.

Options:
    -h, --help              Print this help message.
    -V, --version           Print version.
    -v, --verbose           Enable verbose logging.
    -o, --output <path>     Specify output path.
    -f, --file <path>       Specify music file, will read duration and other
                            information from file. (rssbotlib is needed.)
    -t, --duration <time>   Specify the duration of music.
    -d, --dir <path>        Specify the output directory.''')

    def print_version(self):
        print('convert_lrc.py v1.0.0.0')
        if have_rssbotlib:
            print(f"rssbotlib v{'.'.join(str(s) for s in version())}")
        else:
            print(RSSBOTLIB_NOTFOUND)


def main() -> int:
    cml = Cml(argv[1:])
    dur = None
    if cml.duration is not None:
        if cml.duration <= 0:
            print('Warning: the duration is 0 or less than 0. Ignored.')
        dur = cml.duration
    if cml.file is not None:
        if not have_rssbotlib:
            raise NotImplementedError(RSSBOTLIB_NOTFOUND)
        video_info = VideoInfo()
        if not video_info.parse(cml.file):
            raise Exception(f'Can not parse music file: {cml.file}')
        dur = video_info.duration
        if cml.verbose:
            print(f'Get duration from music file: {dur}')
        metadata = video_info.meta
    if cml.verbose:
        print(f'Duration: {dur}')
    output = None
    if cml.output:
        output = cml.output
    elif cml.file and have_rssbotlib and metadata is not None:
        output = generate_good_filename(metadata)
        if output is not None:
            output = join(dirname(cml.input), output)
            if cml.verbose:
                print(f'Get file name from metadata: {output}')
    if output is None:
        output = splitext(cml.input)[0] + '.lrc'
        if cml.verbose:
            print(f'Get file name from input file: {output}')
    if cml.dir is not None:
        output = join(cml.dir, basename(output))
        print(f'Replace output directory: {output}')


if __name__ == "__main__":
    try:
        exit(main())
    except SystemExit:
        pass
    except:  # noqa: E722
        from traceback import print_exc
        print_exc()
        exit(1)
