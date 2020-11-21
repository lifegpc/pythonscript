# biliReleaseInfo.py
# v1.0.1
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
import xlwt
from requests import Session
from requests.exceptions import RetryError
from os import remove
from os.path import exists
from regex import search, I


class downloaddata:
    ver = None
    origin = None
    linux = None
    mac = None
    windows = None
    windows10_x64 = None
    windows10_x64_exe = None
    windows_x64 = None
    windows_x64_exe = None
    windows_x86 = None
    windows_x86_exe = None

    def __f(self, n):
        return n if n is not None else ''

    def writetosheet(self, a: xlwt.Worksheet, r: int):
        a.write(r, 0, self.__f(self.ver))
        a.write(r, 1, self.__f(self.origin))
        a.write(r, 2, self.__f(self.linux))
        a.write(r, 3, self.__f(self.mac))
        a.write(r, 4, self.__f(self.windows))
        a.write(r, 5, self.__f(self.windows10_x64))
        a.write(r, 6, self.__f(self.windows10_x64_exe))
        a.write(r, 7, self.__f(self.windows_x64))
        a.write(r, 8, self.__f(self.windows_x64_exe))
        a.write(r, 9, self.__f(self.windows_x86))
        a.write(r, 10, self.__f(self.windows_x86_exe))


def writedownloaddata(d: downloaddata, t: dict):
    n = t['name']
    c = t['download_count']
    x = search(r'^bili_\d+\.\d+\.\d+(\.\d+\.[0-9a-f]+)?\.7z$', n, I)
    if x is not None:
        d.origin = c
        return
    x = search(r'^bili_\d+\.\d+\.\d+(\.\d+\.[0-9a-f]+\.)?_linux\.7z$', n, I)
    if x is not None:
        d.linux = c
        return
    x = search(r'^bili_\d+\.\d+\.\d+(\.\d+\.[0-9a-f]+\.)?_mac\.7z$', n, I)
    if x is not None:
        d.mac = c
        return
    x = search(r'^bili_\d+\.\d+\.\d+(\.\d+\.[0-9a-f]+\.)?_windows\.7z$', n, I)
    if x is not None:
        d.windows = c
        return
    x = search(
        r'^bili_\d+\.\d+\.\d+(\.\d+\.[0-9a-f]+\.)?_windows10_x64\.7z$', n, I)
    if x is not None:
        d.windows10_x64 = c
        return
    x = search(
        r'^bili_\d+\.\d+\.\d+(\.\d+\.[0-9a-f]+\.)?_windows10_x64\.exe$', n, I)
    if x is not None:
        d.windows10_x64_exe = c
        return
    x = search(
        r'^bili_\d+\.\d+\.\d+(\.\d+\.[0-9a-f]+\.)?_windows_x64\.7z$', n, I)
    if x is not None:
        d.windows_x64 = c
    x = search(
        r'^bili_\d+\.\d+\.\d+(\.\d+\.[0-9a-f]+\.)?_windows_x64\.exe$', n, I)
    if x is not None:
        d.windows_x64_exe = c
    x = search(
        r'^bili_\d+\.\d+\.\d+(\.\d+\.[0-9a-f]+\.)?_windows_x86\.7z$', n, I)
    if x is not None:
        d.windows_x86 = c
    x = search(
        r'^bili_\d+\.\d+\.\d+(\.\d+\.[0-9a-f]+\.)?_windows_x86\.exe$', n, I)
    if x is not None:
        d.windows_x86_exe = c


fn = 'biliReleaseInfo.xls'
if exists(fn):
    remove(fn)
r = Session()
w = xlwt.Workbook(encoding='utf8')
a: xlwt.Worksheet = w.add_sheet('下载量')
firstl = ['版本', 'origin', 'linux', 'mac', 'windows', 'windows10_x64',
          'windows10_x64_exe', 'windows_x64', 'windows_x64_exe', 'window_x86', 'windows_x86_exe']
firstlc = [1.2, 0.7, 0.5, 0.5, 0.7, 1.2, 1.6, 1.1, 1.5, 1.1, 1.5]
for k in range(len(firstl)):
    a.write(0, k, firstl[k])
    c: xlwt.Column = a.col(k)
    c.width = int(c.width * firstlc[k])
p = 1
row = 1
retry = 0
while True:
    url = f"https://api.github.com/repos/lifegpc/bili/releases?page={p}"
    re = r.get(url)
    if re.ok:
        l = re.json()
        if len(l) == 0:
            break
        for i in l:
            t = downloaddata()
            t.ver = f"{i['tag_name']} beta" if i['prerelease'] else i['tag_name']
            for k in i['assets']:
                writedownloaddata(t, k)
            t.writetosheet(a, row)
            row = row + 1
    else:
        retry = retry + 1
        if retry == 3:
            raise RetryError()
        continue
    p = p + 1
if row > 1:
    a.write(row, 0, '总计')
    zc = 66
    for k in range(10):
        z = chr(zc + k)
        a.write(row, k + 1, xlwt.Formula(f"SUM({z}2:{z}{row})"))
    for i in range(1, row + 1):
        a.write(i, 11, xlwt.Formula(f"SUM(B{i+1}:K{i+1})"))
    a.write(row + 1, 0, '平均')
    for k in range(11):
        z = chr(zc + k)
        a.write(row + 1, k + 1,
                xlwt.Formula(f"SUM({z}2:{z}{row})/COUNTA({z}2:{z}{row})"))
w.save(fn)
