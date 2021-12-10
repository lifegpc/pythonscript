# gen_dlsite.py
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
from hashlib import sha512 as __sha512
from typing import Dict, List
from urllib.parse import quote_plus as q, urlencode
from json import load as loadjson, dumps as dumpjson
from os.path import exists
from requests import Session
from time import time
from traceback import print_exc
from getopt import getopt
from re import search, IGNORECASE
jsonsep = (',', ':')
SHA512_TYPE = 1
ParseQsResult = Dict[str, List[str]]


def sha512(s, encoding='utf8') -> str:
    if isinstance(s, str):
        b = s.encode(encoding)
    elif isinstance(s, bytes):
        b = s
    else:
        b = str(s).encode(encoding)
    h = __sha512()
    h.update(b)
    return h.hexdigest()


def genSign(sercet: str, qd: ParseQsResult, t: int = SHA512_TYPE):
    para = ''
    keys = qd.keys()
    keys = sorted(keys)
    for k in keys:
        if k != 'sign' and qd[k] is not None:
            for qv in qd[k]:
                v = f"{q(k)}={q(qv)}"
                para = v if para == '' else f"{para}&{v}"
    para = sercet + para
    if t & SHA512_TYPE:
        h = sha512(para)
    else:
        h = sha512(para)
    return h


def loadsWithHeaderSep(s: str) -> Dict[str, str]:
    try:
        d = {}
        sl = s.split(';')
        for i in sl:
            i = i.strip()
            ss = i.split('=', 1)
            d[ss[0]] = ss[1]
        return d
    except Exception:
        return None


class Settings:
    def readSettings(self):
        if exists('gen_dlsite.json'):
            try:
                with open('gen_dlsite.json', 'r', encoding='utf8') as f:
                    self.__data = loadjson(f)
            except Exception:
                self.__data = None
        else:
            self.__data = None

    @property
    def APIEntry(self) -> str:
        '''Source code of API:
        https://github.com/lifegpc/csweb/tree/master/proxy'''
        defalut = 'https://cs.kanahanazawa.com/proxy'
        if self.__data is None:
            return defalut
        key = 'APIEntry'
        if key in self.__data and self.__data[key]:
            return self.__data[key]
        return defalut

    @property
    def APISecrets(self) -> str:
        if self.__data is None:
            return None
        key = 'APISecrets'
        if key in self.__data and self.__data[key] and self.__data[key] != '':
            return self.__data[key]
        return None

    @property
    def dlsiteCookies(self) -> Dict[str, str]:
        if self.__data is None:
            return None
        key = 'dlsiteCookies'
        if key in self.__data and self.__data[key] and self.__data[key] != '':
            return loadsWithHeaderSep(self.__data[key])
        return None

    @property
    def overrideOld(self) -> bool:
        defalut = False
        if self.__data is None:
            return defalut
        key = 'overrideOld'
        if key in self.__data and isinstance(self.__data[key], bool):
            return self.__data[key]
        return defalut


class Main:
    def __init__(self):
        self._s = Settings()
        self._s.readSettings()
        self._ses = Session()
        self._dlses = Session()

    def add(self, id: str, cookies: Dict[str, str]):
        try:
            r = self.request('post', 'add', id=id, cookies=cookies,
                             headers={"referrer": "https://www.dlsite.com/"})
            if r.status_code == 200:
                j = r.json()
                if j['code'] != 0:
                    print(f"{j['code']} {j['msg']}")
                    return None
                return j['result']
            else:
                print(f'{r.status_code} {r.reason}')
                return None
        except Exception:
            print_exc()
            return None

    @property
    def APIEntry(self) -> str:
        return self._s.APIEntry

    @property
    def APISecrets(self) -> str:
        return self._s.APISecrets

    @property
    def dlsiteCookies(self) -> Dict[str, str]:
        return self._s.dlsiteCookies

    def exists(self, id: str) -> bool:
        try:
            r = self.request('post', 'exists', id=id)
            if r.status_code == 200:
                j = r.json()
                if j['code'] != 0:
                    print(f"{j['code']} {j['msg']}")
                    return None
                return j['result']
            else:
                print(f'{r.status_code} {r.reason}')
                return None
        except Exception:
            print_exc()
            return None

    def gen(self, id: str, target: str) -> str:
        try:
            r = self.request('post', 'gen', id=id, target=target,
                             e=round(time() + 3600))
            if r.status_code == 200:
                j = r.json()
                if j['code'] != 0:
                    print(f"{j['code']} {j['msg']}")
                    return None
                return j['result']
            else:
                print(f'{r.status_code} {r.reason}')
                return None
        except Exception:
            print_exc()
            return None

    def getCookies(self) -> Dict[str, str]:
        d = {}
        for i in self._dlses.cookies.iteritems():
            d[i[0]] = i[1]
        return d

    def getName(self, link: str) -> str:
        if link is None:
            return None
        rs = search(r'product_id/([^./]+)', link, IGNORECASE)
        if rs is None:
            return None
        pn = rs.groups()[0]
        rs = search(r'number/(\d+)', link, IGNORECASE)
        if rs is not None:
            pn += '.part' + rs.groups()[0]
        return pn

    def getopt(self, argv: List[str]):
        ll = getopt(argv, '', [])
        self._link = None
        if len(ll[1]) > 0:
            self._link = ll[1][0]

    def getProxyLink(self, link):
        r = self._dlses.head(link)
        if r.status_code not in [301, 302, 307]:
            print(f'{r.status_code} {r.reason}')
            return None
        url = r.headers['location']
        pn = self.getName(link)
        if not self.overrideOld:
            tpn = pn
            tpni = 0
            ext = self.exists(tpn)
            if ext is None:
                return None
            while ext is True:
                tpni += 1
                tpn = f'{pn}_{tpni}'
                ext = self.exists(tpn)
                if ext is None:
                    return None
            pn = tpn
        print(pn)
        ck = self.getCookies()
        if ck is None:
            return None
        r = self.add(pn, ck)
        if not r:
            return None
        r = self.gen(pn, url)
        if r:
            return r
        return None

    @property
    def link(self) -> str:
        if hasattr(self, '_link'):
            return self._link
        else:
            return None

    def isDownloadLink(self) -> bool:
        if self.link is None:
            return False
        return self.link.find('download') > -1

    def isSerialLink(self) -> bool:
        if self.link is None:
            return False
        return self.link.find('serial') > -1

    @property
    def name(self) -> str:
        return self.getName(self.link)

    def overrideOld(self) -> bool:
        return self._s.overrideOld

    def request(self, method: str, action: str, stream: bool = False, **kw):
        url = f'{self.APIEntry}/{action}'
        se = {'t': [str(round(time()))], 'a': [action]}
        for i in kw:
            c = kw[i]
            if isinstance(c, (list, dict)):
                se[i] = [dumpjson(c, ensure_ascii=False, separators=jsonsep)]
            elif isinstance(c, str):
                se[i] = [c]
            else:
                se[i] = [str(c)]
        sg = genSign(self.APISecrets, se)
        se['sign'] = [sg]
        for i in se:
            se[i] = se[i][0]
        re = self._ses.request(method, url, data=se, stream=stream)
        return re

    def run(self, argv: List[str]) -> int:
        if self.APISecrets is None:
            print('APISecrets is needed.')
            return -1
        if self.dlsiteCookies is None:
            print('dlsiteCookies is needed.')
            return -2
        self.getopt(argv)
        self._dlses.cookies.update(self.dlsiteCookies)
        self._dlses.headers.update({'referrer': 'https://www.dlsite.com/'})
        if self.link is None:
            print('gen_dlsite.py [options] <link>')
            return -3
        if self.isDownloadLink:
            t = self.getProxyLink(self.link)
            if t:
                print(t)
        elif self.isSerialLink:
            pass
        else:
            print('Unknown link.')
            return -4
        return 0


if __name__ == "__main__":
    import sys
    try:
        m = Main()
        sys.exit(m.run(sys.argv[1:]))
    except Exception:
        print_exc()
        sys.exit(-1)
