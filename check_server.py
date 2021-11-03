from getopt import GetoptError, getopt
from json import load as loadjson, dump as savejson
from os.path import exists
from socket import AF_INET, SOCK_STREAM, socket, timeout as SocketTimeout
from ssl import (
    CERT_REQUIRED,
    SSLCertVerificationError,
    match_hostname,
    wrap_socket,
)
from typing import List, Optional
from urllib.parse import ParseResult, urlparse
import xml.etree.ElementTree as ET


class Settings:
    def readSettings(self, fn: str = None):
        if fn is None:
            fn = 'check_server.json'
        if exists(fn):
            try:
                with open(fn, 'r', encoding='utf8') as f:
                    self.__data = loadjson(f)
            except Exception:
                self.__data = None
        else:
            self.__data = None

    @property
    def ca_certs(self) -> Optional[str]:
        if self.__data is None:
            return None
        key = 'ca_certs'
        if key in self.__data and self.__data[key] and self.__data[key] != '':
            return self.__data[key]
        return None

    @property
    def ca_match_host(self) -> bool:
        default = True
        if self.__data is None:
            return default
        key = 'ca_match_host'
        if key in self.__data and isinstance(self.__data[key], bool):
            return self.__data[key]
        return default


class Opts:
    def __init__(self, cm: List[str]) -> None:
        try:
            r = getopt(cm, 'c:v', ["config=", "ca_certs=", "verbose"])
            for i in r[0]:
                if i[0] in ['-c', '--config']:
                    self._config = i[1]
                elif i[0] == 'ca_certs':
                    self._ca_certs = i[2]
                elif i[0] in ['-v', '--verbose']:
                    self._verbose = True
            if len(r[1]) < 2:
                raise GetoptError('result_xml and url is needed.')
            self.xml = r[1][0]
            self.urls: List[ParseResult] = []
            for i in r[1][1:]:
                self.urls.append(urlparse(i))
        except GetoptError as e:
            from sys import exit
            print(e.msg)
            self.print_help()
            exit(-1)

    @property
    def ca_certs(self) -> Optional[str]:
        if hasattr(self, "_ca_certs"):
            return self._ca_certs

    @property
    def config(self) -> Optional[str]:
        if hasattr(self, "_config"):
            return self._config

    def print_help(self) -> None:
        print('''Usage: check_server.py [Options] <result_xml> <url> [<url>]
Options:

    -c, --config <path>     Specify config file
        --ca_certs <path>   Specify certificate file
    -v, --verbose           Enable verbose logging.''')

    @property
    def verbose(self) -> bool:
        if hasattr(self, "_verbose"):
            return self._verbose
        return False


class ResultReader:
    def __init__(self, fn: str, opt: Opts) -> None:
        self._tree = ET.parse(fn)
        self._root = self._tree.getroot()
        self._hosts = self._root.findall('host')
        self._len = len(self._hosts)

    def __iter__(self):
        self._i = 0
        return self

    def __len__(self):
        return self._len

    def __next__(self):
        if self._i >= self._len:
            raise StopIteration
        r = self.get(self._i)
        self._i += 1
        return r

    def get(self, i):
        if i >= self._len or i < -self._len:
            return None
        r = self._hosts[i]
        ad = r.find('address')
        if ad is None:
            return None
        return ad.get('addr')


class Main:
    def __init__(self, se: Settings, opt: Opts) -> None:
        self._crt = opt.ca_certs if opt.ca_certs is not None else se.ca_certs
        self._opt = opt
        self._se = se
        if self._crt is None:
            raise ValueError('Certificate files not specified.')
        if opt.verbose:
            print(f'CA Files: {self._crt}')
        self._te = {}
        self._match_host = se.ca_match_host

    def check(self, ip: str, url: ParseResult) -> bool:
        if url.hostname in self._te:
            if ip in self._te[url.hostname]:
                if self._opt.verbose:
                    print(f'Skip {ip} ({url.hostname})')
                    return False
        self._s = socket(AF_INET, SOCK_STREAM)
        self._ssl = wrap_socket(self._s, ca_certs=self._crt,
                                cert_reqs=CERT_REQUIRED)
        timeout = 10
        self._ssl.settimeout(timeout)
        try:
            self._ssl.connect((ip, 443))
            if self._match_host:
                match_hostname(self._ssl.getpeercert(), url.hostname)
            if url.query != '':
                p = url.path + '?' + url.query
            else:
                p = url.path
            text = f'GET {p} HTTP/1.1\r\n'
            text += f'Accept: */*\r\nHost: {url.hostname}\r\n'
            text += 'Connection: Keep-Alive\r\n'
            if self._opt.verbose:
                print(ip)
                print(text)
            self._ssl.send(bytes(text + '\r\n', 'utf-8'))
            data = str(self._ssl.recv(2048), 'utf-8')
            if self._opt.verbose:
                print(data)
            code = data.split()[1]
            if self._opt.verbose:
                print(f'Code: {code}')
            ok = False
            if code == '200':
                ok = True
            self._ssl.close()
            self._s.close()
            return ok
        except SSLCertVerificationError as e:
            print(ip, e.args)
            if url.hostname not in self._te:
                self._te[url.hostname] = []
            self._te[url.hostname].append(ip)
            self._ssl.close()
            self._s.close()
            return False
        except SocketTimeout:
            print(f"{ip} timeout")
            self._ssl.close()
            self._s.close()
            return False
        except Exception:
            from traceback import print_exc
            print(ip)
            print_exc()
            self._ssl.close()
            self._s.close()
            return False


def main():
    import sys
    opt = Opts(sys.argv[1:])
    se = Settings()
    se.readSettings(opt.config)
    r = ResultReader(opt.xml, opt)
    m = Main(se, opt)
    re = {}
    try:
        for u in opt.urls:
            for i in r:
                if u.hostname in re:
                    if i in re[u.hostname]:
                        if opt.verbose:
                            print(f'Skip {i} ({u.hostname})')
                        continue
                if m.check(i, u):
                    if u.hostname not in re:
                        re[u.hostname] = []
                    re[u.hostname].append(i)
                    print(f'Add {i} to {u.hostname}')
    except KeyboardInterrupt:
        c = ''
        while c != 'y' and c != 'n':
            c = input('Do u want to save result?(y/n)')
        if c == 'n':
            from sys import exit
            exit(0)
    with open('result.json', 'w', encoding='UTF-8') as f:
        savejson(re, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
