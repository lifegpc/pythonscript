# check.py
# (C) 2020 lifegpc
# The repo location: https://github.com/lifegpc/pythonscript
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from getopt import getopt
import sys
from os import listdir
from os.path import getsize, exists
from re import search
from subprocess import Popen, PIPE
from json import dumps, loads


def help():
    print('''命令行帮助：
    check.py -c filename    校验指定JSON文件里的文件
    check.py -g filename [ext1 ext2 ...]    生成JSON校验文件
    ext1等是要生成校验的文件的扩展名
    如不知道默认列表为"mp4 webm m4a"。
    注：程序需要UNIX工具sha256sum才能工作''')


def isok(fn: str, ext: list) -> bool:
    ex = fn.split('.')[-1]
    for i in ext:
        if ex == i:
            return True
    return False


def getfilelist(path: str = ".", ext: list = ['mp4', 'webm', 'm4a']) -> list:
    l = listdir(path)
    r = []
    for i in l:
        if isok(i, ext):
            r.append(i)
    return r


def getsha256(fn: str) -> str:
    p = Popen(f'sha256sum "{fn}"', shell=True, stdout=PIPE)
    f = p.stdout
    r = f.read().decode('utf8')
    rs = search(r'([0-9a-f]+)', r)
    if rs is not None:
        return rs.groups()[0]
    else:
        raise Exception(f"ERROR:{r}")


def main(opt: dict):
    if 'g' in opt:
        if 'ext' in opt:
            file_list = getfilelist(ext=opt['ext'])
        else:
            file_list = getfilelist()
        result = []
        ii = 1
        l = len(file_list)
        for i in file_list:
            t = {}
            print(f'\r [{ii}/{l}]"{i}"', end='')
            t['filename'] = i
            t['size'] = getsize(i)
            t['sha256'] = getsha256(i)
            result.append(t)
            ii = ii+1
        f = open(opt['o'], 'w', encoding='utf8')
        f.write(dumps(result))
        f.close()
    elif 'c' in opt:
        f = open(opt['o'], 'r', encoding='utf8')
        file_list = loads(f.read())
        f.close()
        ii = 1
        l = len(file_list)
        for i in file_list:
            fn = i['filename']
            print(f'\r [{ii}/{l}]"{fn}"', end='')
            if exists(fn):
                if getsize(fn) != i['size']:
                    print(f'\r文件大小不一致："{fn}"')
                if getsha256(fn) != i['sha256']:
                    print(f'\r文件sha256散列值不一致："{fn}"')
            else:
                print(f'\r找不到文件："{fn}"')
            ii = ii+1
    else:
        help()


if len(sys.argv) > 1:
    ch = getopt(sys.argv[1:], 'gch')
    r = {}
    for i in ch[0]:
        if i[0] == '-g':
            r['g'] = True
        if i[0] == '-c':
            r['c'] = True
        if i[0] == '-h':
            help()
            exit()
    if len(ch[1]) > 0:
        r['o'] = ch[1][0]
        ext = []
        if len(ch[1]) > 1:
            for i in ch[1][1:]:
                ext.append(i)
        if len(ext) > 1:
            r['ext'] = ext
        main(r)
    else:
        help()
else:
    help()
