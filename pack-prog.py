# pack-prog.py
# (C) 2021 lifegpc
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
from os import system, devnull, environ, remove
from getopt import getopt
from typing import List
from sys import argv, exit
from subprocess import Popen, PIPE
from re import search, IGNORECASE
from os.path import splitext, exists, abspath
from tempfile import NamedTemporaryFile


def add_path_ext(path: str) -> str:
    p, n = splitext(path)
    if n != '':
        return path
    else:
        pext = environ['PATHEXT']
        pextl = pext.split(';')
        for ext in pextl:
            if ext == '':
                continue
            if exists(p + ext):
                return p + ext
    return path


def check_needed_prog():
    if system(f'ldd --help > {devnull}'):
        return False
    if system(f'7z --help > {devnull}'):
        return False
    return True


def check_prog(prog: str) -> List[str]:
    r = Popen(f'ldd {prog}', stdout=PIPE, stderr=PIPE)
    out: bytes = r.communicate()[0]
    r.wait()
    out += r.communicate()[0]
    if not r.returncode:
        sl = out.splitlines(False)
        rl = []
        for r in sl:
            r = r.decode()
            rs = search(r'=?-?> (.+) ?(\(0x[0-9a-f]+\))?$', r, IGNORECASE)
            if rs is not None:
                rl.append(abspath(rs.groups()[0]))
            else:
                raise ValueError(f'Can not find path for {r}.')
        return rl
    return None


def getUnixPath(path: str) -> str:
    rs = search(r'^[A-Z]:', path, IGNORECASE)
    if rs is None:
        return path.replace('\\', '/')
    return '/' + path[0].lower() + path[2:].replace('\\', '/')


def getWindowsPath(path: str) -> str:
    rs = search(r'^[\\/][A-Z][\\/]', path, IGNORECASE)
    if rs is None:
        return path.replace('/', '\\')
    return path[1].upper() + ":" + path[2:].replace('/', '\\')


def print_help():
    print('''pack-prog.py [-o <output_name>] [programs]''')


class Prog:
    def __init__(self):
        self._loc = []

    def add_dep(self, path: str):
        path_w = getWindowsPath(path)
        if path_w.upper().startswith('C:\\WINDOWS'):
            return
        if path_w not in self._loc:
            print(f'add dependence: "{path_w}"')
            self._loc.append(path_w)

    def add_prog(self, path: str):
        pro = add_path_ext(path)
        pro_w = getWindowsPath(pro)
        if pro_w not in self._loc:
            print(f'add program: "{pro_w}"')
            self._loc.append(pro_w)

    def to_7z(self, output: str):
        p = NamedTemporaryFile(delete=False)
        for i in self._loc:
            p.write((i + '\n').encode('UTF8'))
        fp = p.name
        p.close()
        try:
            system(f'7z a -mmt1 -mx9 -y {output} @{fp}')
        except Exception:
            remove(fp)
            from traceback import print_exc
            print_exc()
        remove(fp)


def main(prog: List[str], output: str = None):
    if output is None:
        output = 'prog.7z'
    if not check_needed_prog():
        print('ldd and 7z is needed.')
    p = Prog()
    for pro in prog:
        pro = abspath(pro)
        pro = add_path_ext(pro)
        # pro_u = getUnixPath(pro)
        rel = check_prog(pro)
        if rel is None:
            print(f'Can not get dependencies for {pro},')
            exit(-1)
        p.add_prog(pro)
        for i in rel:
            p.add_dep(i)
    p.to_7z(output)


if __name__ == "__main__":
    if len(argv) > 1:
        d = getopt(argv[1:], 'o:')
        output = None
        if len(d[0]):
            for i in d[0]:
                if i[0] == '-o':
                    output = i[1]
                    break
        main(d[1], output)
    else:
        print_help()
