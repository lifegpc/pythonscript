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
from os.path import exists, getsize, split, isdir, isfile, relpath
from os import listdir
from hashlib import md5
import sys
from time import time


def listdirc(path: str, path2: str = None):
    if path2 is None and path[-1] != '/' and path[-1] != '\\':
        path2 = path + '/'
    elif path2 is None:
        path2 = path
    l = listdir(path)
    r = []
    for i in l:
        fn = f'{path}/{i}'
        if exists(fn):
            if isfile(fn):
                r.append({'fn': fn, 'path': path2})
            elif isdir(fn):
                r = r + listdirc(fn, path2)
    return r


limit_size = 256 * 1024

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filel = sys.argv[1:]
    else:
        filel = ['.']
    file_list = []
    for i in filel:
        if exists(i):
            if isfile(i):
                file_list.append({'fn': i, 'path': ''})
            elif isdir(i):
                file_list = file_list + listdirc(i)
    e = 1
    l = len(file_list)
    f2 = open('bdshare.txt', 'w', encoding='utf8')
    for j in file_list:
        i = j['fn']
        if exists(i):
            fs = getsize(i)
            with open(i, 'rb', 1024) as f:
                md = md5()
                r = 0
                t1 = time()
                t = f.read(1024)
                while len(t) > 0:
                    r += len(t)
                    md.update(t)
                    if r == limit_size:
                        md51 = md.hexdigest()
                    t2 = time()
                    if t2 > t1 + 1:
                        t1 = t2
                        print(f"\r[{e}/{l}]{'%.2f'%(r/fs*100)}%", end='')
                    t = f.read(1024)
                md52 = md.hexdigest()
                if fs < limit_size:
                    md51 = md52
                if j['path'] != "":
                    pa = relpath(i, j["path"])
                else:
                    pa = split(i)[1]
                share = f'{md52}#{md51}#{fs}#{pa}'
                f2.write(share+'\n')
                print(f"\r[{e}/{l}]:{share}")
        e = e + 1
    f2.close()
