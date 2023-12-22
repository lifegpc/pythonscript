from getopt import gnu_getopt as getopt, GetoptError
from math import floor
from os.path import basename, dirname, join, splitext
from re import compile, Match, search
from sys import argv, exit
from typing import List, Optional
try:
    from _rssbotlib import AVDict, version, VideoInfo
    have_rssbotlib = True
except ImportError:
    AVDict = None
    have_rssbotlib = False


RSSBOTLIB_NOTFOUND = '''rssbotlib not found.
The source code is available at https://github.com/lifegpc/ffmpeg-study/tree/master/rssbotlib'''  # noqa: E501
DUR_REG = compile(r'^(?P<sign>[\+-])?(((?P<h>\d+):)?((?P<min>\d+):))?(?P<sec>\d+)(\.(?P<ms>\d+))?$')  # noqa: E501
LRCDUR_REG = compile(r'\[(((?P<h>\d+):)?((?P<min>\d+):))?(?P<sec>\d+)(\.(?P<ms>\d+))?\]')  # noqa: E501


def convert_dur(r: Match) -> float:
    rd = r.groupdict()
    t = int(rd['sec'])
    if rd['ms']:
        t += int(rd['ms']) / (10 ** len(rd['ms']))
    if rd['min']:
        t += int(rd['min']) * 60
    if rd['h']:
        t += int(rd['h']) * 3600
    if 'sign' in rd and rd['sign'] == '-':
        t = -t
    return t


def prase_duration(s: str) -> float:
    r = search(DUR_REG, s)
    if r is None:
        raise ValueError(f'Can not parse duration "{s}"')
    return convert_dur(r)


def generate_good_filename(meta: AVDict) -> Optional[str]:
    m = meta.to_dict()
    if 'title' in m and 'artist' in m:
        return f"{m['artist']} - {m['title']}.lrc"
    elif 'title' in m:
        return f"{m['title']}.lrc"


class Lyric:
    def __init__(self) -> None:
        self._l = []
        self._meta = []
        self._bom = False
        self._has_dur = True

    def apply_offset(self):
        offset = None
        for m in self._meta:
            if m.startswith('offset:'):
                offset = int(m.lstrip('offset:'))
                self._meta.remove(m)
                break
        if offset is None:
            return
        for i in self._l:
            i['time'] = max(0, round((i['time'] * 1000 + offset) / 1000, 2))

    def convert_translate_type(self, dur: Optional[float]):
        self._l.sort(key=lambda d: d['time'])
        re = []
        ltmp = 0
        tmp = None
        for i in self._l:
            if tmp is not None:
                re.append({'time': max(ltmp, round(i['time'] - 0.01, 2)),
                           'data': tmp})
                tmp = None
            elif i['time'] == ltmp:
                if tmp is None:
                    tmp = i['data']
                else:
                    re.append({'time': ltmp, 'data': tmp})
                    tmp = i['data']
                continue
            s: str = i['data']
            if s.find(' / ') > 0:
                li = s.split(' / ', 1)
                ltmp = i['time']
                tmp = li[1]
                re.append({'time': i['time'], 'data': li[0]})
            else:
                ltmp = i['time']
                re.append(i.copy())
        if tmp is not None:
            if dur is not None:
                re.append({'time': max(round(dur, 2), round(ltmp + 0.01, 2)),
                           'data': tmp})
        self._l = re

    def parse(self, fn: str):
        li = []
        me = []
        with open(fn, 'r', encoding='UTF-8') as f:
            t = f.read(1)
            if t == '\ufeff':
                self._bom = True
            else:
                f.seek(0, 0)
            ll = f.readlines(1)
            while len(ll) > 0:
                for i in ll:
                    i = i.rstrip('\n')
                    if self._has_dur:
                        tre = LRCDUR_REG.finditer(i)
                        re: List[Match] = []
                        for tmp in tre:
                            re.append(tmp)
                        if len(re) == 0:
                            if i.startswith('[') and i.endswith(']'):
                                me.append(i[1:-1])
                            else:
                                if len(li) == 0:
                                    self._has_dur = False
                                    li.append(i)
                                else:
                                    print(f'Ignored "{i}"')
                        else:
                            d = i[re[-1].end():]
                            for r in re:
                                li.append({'time': round(convert_dur(r), 2),
                                           'data': d})
                    else:
                        if i.startswith('[') and i.endswith(']'):
                            me.append(i[1:-1])
                        else:
                            li.append(i)
                ll = f.readlines(1)
        self._l = li
        self._meta = me

    def save(self, fn: str):
        with open(fn, 'w', encoding='UTF-8') as f:
            if self._bom:
                f.write('\ufeff')
            for m in self._meta:
                f.write(f"[{m}]\n")
            for i in self._l:
                if isinstance(i, str):
                    f.write(f"{i}\n")
                else:
                    t = round(i['time'] * 100)
                    m = floor(t / 6000)
                    s = floor((t % 6000) / 100)
                    ms = t % 100
                    f.write(f"[{m:02}:{s:02}.{ms:02}]{i['data']}\n")


class Cml:
    def __init__(self, arg: List[str]) -> None:
        self.output = None
        self.file = None
        self.verbose = False
        self.duration = None
        self.dir = None
        self.offset = False
        if len(arg) == 0:
            self.print_help()
            exit(0)
        try:
            r = getopt(arg, '-hVvo:f:t:d:',
                       ['help', 'version', 'verbose', 'output=', 'file=',
                        'duration=', 'dir=', 'offset'])
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
                elif i[0] == '--offset':
                    self.offset = True
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
    -d, --dir <path>        Specify the output directory.
        --offset            Remove offset tag in lryic file and apply offset
                            for lyric''')

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
        if cml.verbose:
            print(f'Replace output directory: {output}')
    lrc = Lyric()
    lrc.parse(cml.input)
    if not lrc._has_dur:
        raise ValueError("This lyric file don't have timestamp.")
    lrc.convert_translate_type(dur)
    if cml.offset:
        lrc.apply_offset()
    lrc.save(output)


if __name__ == "__main__":
    try:
        exit(main())
    except SystemExit:
        pass
    except:  # noqa: E722
        from traceback import print_exc
        print_exc()
        exit(1)
