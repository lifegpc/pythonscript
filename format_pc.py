# format_pc.py
# v1.0.0
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
from platform import system
from os.path import exists, abspath
from os import remove, rename
import sys
from re import compile, IGNORECASE
from typing import Dict


REG = compile(r'\${([a-z_]+)}', IGNORECASE)
REG2 = compile(r'/([a-z])/', IGNORECASE)
REG3 = compile(r'^(Name|Description|Version|Requires|Requires.private|Conflicts|Cflags):', IGNORECASE)  # noqa: E501
REG4 = compile(r'^Libs(\.private)?:', IGNORECASE)


def replace_v(inp: str, vd: Dict[str, str]) -> str:
    re = REG.search(inp)
    while re is not None:
        k = re.groups()[0]
        v = vd[k] if k in vd else ''
        inp = inp.replace(re.group(), v)
        re = REG.search(inp)
    return inp


def format_path(inp: str) -> str:
    if system() == "Windows":
        re = REG2.search(inp)
        if re is None:
            return abspath(inp).replace("\\", "/")
        else:
            return abspath(inp.replace(re.group(), re.groups()[0].upper() + ":/")).replace("\\", "/")  # noqa: E501
    return inp


def format_lib(inp: str) -> str:
    li = inp.split(" ")
    o = ''
    for i in li:
        s = i.strip()
        if s.endswith(".lib"):
            o += f' -l{s[:-4]}'
        elif s.startswith("-libpath:"):
            p = format_path(s[9:])
            o += f' -L{p}'
        else:
            o += f' {s}'
    return o


def parse_pc(fn: str):
    if not exists(fn):
        return
    with open(fn, 'r', encoding='UTF-8') as f:
        t = f.read()
    li = t.splitlines(False)
    vd = {}
    if exists(fn + '.tmp'):
        remove(fn + '.tmp')
    with open(fn + '.tmp', 'w', encoding='UTF-8') as f:
        for i in li:
            s = i.strip()
            if s.startswith("#") or len(s) == 0:
                f.write(i + '\n')
            elif REG3.search(s) is not None:
                f.write(i + '\n')
            elif REG4.search(s) is not None:
                ll = s.split(':', 1)
                v = replace_v(ll[1], vd)
                v = format_lib(v)
                f.write(f"{ll[0]}:{v}\n")
            elif s.find('=') > -1:
                ll = s.split('=', 1)
                v = replace_v(ll[1], vd)
                v = format_path(v)
                vd[ll[0]] = v
                f.write(f"{ll[0]}={v}\n")
    remove(fn)
    rename(fn + '.tmp', fn)
    print(f'formated {fn}')


for i in sys.argv[1:]:
    parse_pc(i)
