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
from os.path import exists, getsize, split
from hashlib import md5
import sys
from time import time

limit_size = 256 * 1024

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_list = sys.argv[1:]
    else:
        print('未输入文件')
        exit(-1)
    e = 1
    l = len(file_list)
    for i in file_list:
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
                print(f"\r[{e}/{l}]:{md52}#{md51}#{fs}#{split(i)[1]}")
        e = e + 1
