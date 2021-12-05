from requests import Session
from http.cookiejar import MozillaCookieJar
from html.parser import HTMLParser
from typing import List, Tuple, Optional
from js2py import eval_js
from os import makedirs, remove
from os.path import join, exists, relpath
from traceback import print_exc
from json import load, dump
from urllib.parse import urljoin, parse_qs, urlparse
from base64 import b64decode as _b64decode
from re import compile
from argparse import ArgumentParser, RawTextHelpFormatter
from textwrap import wrap as _wrap
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile


def wrap(s: str, width: int = 56):
    return '\n'.join(_wrap(s, width))


def b64decode(s):
    m = len(s) % 4
    if m != 0:
        if isinstance(s, bytes):
            s += b'=' * (4 - m)
        elif isinstance(s, str):
            s += '=' * (4 - m)
    return _b64decode(s)


KEY_REG = compile(rb'([^\d]+\d)')
MW = [99, 124, 119, 123, 242, 107, 111, 197, 48, 1, 103, 43, 254, 215, 171, 118, 202, 130, 201, 125, 250, 89, 71, 240, 173, 212, 162, 175, 156, 164, 114, 192, 183, 253, 147, 38, 54, 63, 247, 204, 52, 165, 229, 241, 113, 216, 49, 21, 4, 199, 35, 195, 24, 150, 5, 154, 7, 18, 128, 226, 235, 39, 178, 117, 9, 131, 44, 26, 27, 110, 90, 160, 82, 59, 214, 179, 41, 227, 47, 132, 83, 209, 0, 237, 32, 252, 177, 91, 106, 203, 190, 57, 74, 76, 88, 207, 208, 239, 170, 251, 67, 77, 51, 133, 69, 249, 2, 127, 80, 60, 159, 168, 81, 163, 64, 143, 146, 157, 56, 245, 188, 182, 218, 33, 16, 255, 243, 210, 205, 12, 19, 236, 95, 151, 68, 23, 196, 167, 126, 61, 100, 93, 25, 115, 96, 129, 79, 220, 34, 42, 144, 136, 70, 238, 184, 20, 222, 94, 11, 219, 224, 50, 58, 10, 73, 6, 36, 92, 194, 211, 172, 98, 145, 149, 228, 121, 231, 200, 55, 109, 141, 213, 78, 169, 108, 86, 244, 234, 101, 122, 174, 8, 186, 120, 37, 46, 28, 166, 180, 198, 232, 221, 116, 31, 75, 189, 139, 138, 112, 62, 181, 102, 72, 3, 246, 14, 97, 53, 87, 185, 134, 193, 29, 158, 225, 248, 152, 17, 105, 217, 142, 148, 155, 30, 135, 233, 206, 85, 40, 223, 140, 161, 137, 13, 191, 230, 66, 104, 65, 153, 45, 15, 176, 84, 187, 22]
SW = [82, 9, 106, 213, 48, 54, 165, 56, 191, 64, 163, 158, 129, 243, 215, 251, 124, 227, 57, 130, 155, 47, 255, 135, 52, 142, 67, 68, 196, 222, 233, 203, 84, 123, 148, 50, 166, 194, 35, 61, 238, 76, 149, 11, 66, 250, 195, 78, 8, 46, 161, 102, 40, 217, 36, 178, 118, 91, 162, 73, 109, 139, 209, 37, 114, 248, 246, 100, 134, 104, 152, 22, 212, 164, 92, 204, 93, 101, 182, 146, 108, 112, 72, 80, 253, 237, 185, 218, 94, 21, 70, 87, 167, 141, 157, 132, 144, 216, 171, 0, 140, 188, 211, 10, 247, 228, 88, 5, 184, 179, 69, 6, 208, 44, 30, 143, 202, 63, 15, 2, 193, 175, 189, 3, 1, 19, 138, 107, 58, 145, 17, 65, 79, 103, 220, 234, 151, 242, 207, 206, 240, 180, 230, 115, 150, 172, 116, 34, 231, 173, 53, 133, 226, 249, 55, 232, 28, 117, 223, 110, 71, 241, 26, 113, 29, 41, 197, 137, 111, 183, 98, 14, 170, 24, 190, 27, 252, 86, 62, 75, 198, 210, 121, 32, 154, 219, 192, 254, 120, 205, 90, 244, 31, 221, 168, 51, 136, 7, 199, 49, 177, 18, 16, 89, 39, 128, 236, 95, 96, 81, 127, 169, 25, 181, 74, 13, 45, 229, 122, 159, 147, 201, 156, 239, 160, 224, 59, 77, 174, 42, 245, 176, 200, 235, 187, 60, 131, 83, 153, 97, 23, 43, 4, 126, 186, 119, 214, 38, 225, 105, 20, 99, 85, 33, 12, 125]
TW = [0, 14, 28, 18, 56, 54, 36, 42, 112, 126, 108, 98, 72, 70, 84, 90, 224, 238, 252, 242, 216, 214, 196, 202, 144, 158, 140, 130, 168, 166, 180, 186, 219, 213, 199, 201, 227, 237, 255, 241, 171, 165, 183, 185, 147, 157, 143, 129, 59, 53, 39, 41, 3, 13, 31, 17, 75, 69, 87, 89, 115, 125, 111, 97, 173, 163, 177, 191, 149, 155, 137, 135, 221, 211, 193, 207, 229, 235, 249, 247, 77, 67, 81, 95, 117, 123, 105, 103, 61, 51, 33, 47, 5, 11, 25, 23, 118, 120, 106, 100, 78, 64, 82, 92, 6, 8, 26, 20, 62, 48, 34, 44, 150, 152, 138, 132, 174, 160, 178, 188, 230, 232, 250, 244, 222, 208, 194, 204, 65, 79, 93, 83, 121, 119, 101, 107, 49, 63, 45, 35, 9, 7, 21, 27, 161, 175, 189, 179, 153, 151, 133, 139, 209, 223, 205, 195, 233, 231, 245, 251, 154, 148, 134, 136, 162, 172, 190, 176, 234, 228, 246, 248, 210, 220, 206, 192, 122, 116, 102, 104, 66, 76, 94, 80, 10, 4, 22, 24, 50, 60, 46, 32, 236, 226, 240, 254, 212, 218, 200, 198, 156, 146, 128, 142, 164, 170, 184, 182, 12, 2, 16, 30, 52, 58, 40, 38, 124, 114, 96, 110, 68, 74, 88, 86, 55, 57, 43, 37, 15, 1, 19, 29, 71, 73, 91, 85, 127, 113, 99, 109, 215, 217, 203, 197, 239, 225, 243, 253, 167, 169, 187, 181, 159, 145, 131, 141]
UW = [0, 11, 22, 29, 44, 39, 58, 49, 88, 83, 78, 69, 116, 127, 98, 105, 176, 187, 166, 173, 156, 151, 138, 129, 232, 227, 254, 245, 196, 207, 210, 217, 123, 112, 109, 102, 87, 92, 65, 74, 35, 40, 53, 62, 15, 4, 25, 18, 203, 192, 221, 214, 231, 236, 241, 250, 147, 152, 133, 142, 191, 180, 169, 162, 246, 253, 224, 235, 218, 209, 204, 199, 174, 165, 184, 179, 130, 137, 148, 159, 70, 77, 80, 91, 106, 97, 124, 119, 30, 21, 8, 3, 50, 57, 36, 47, 141, 134, 155, 144, 161, 170, 183, 188, 213, 222, 195, 200, 249, 242, 239, 228, 61, 54, 43, 32, 17, 26, 7, 12, 101, 110, 115, 120, 73, 66, 95, 84, 247, 252, 225, 234, 219, 208, 205, 198, 175, 164, 185, 178, 131, 136, 149, 158, 71, 76, 81, 90, 107, 96, 125, 118, 31, 20, 9, 2, 51, 56, 37, 46, 140, 135, 154, 145, 160, 171, 182, 189, 212, 223, 194, 201, 248, 243, 238, 229, 60, 55, 42, 33, 16, 27, 6, 13, 100, 111, 114, 121, 72, 67, 94, 85, 1, 10, 23, 28, 45, 38, 59, 48, 89, 82, 79, 68, 117, 126, 99, 104, 177, 186, 167, 172, 157, 150, 139, 128, 233, 226, 255, 244, 197, 206, 211, 216, 122, 113, 108, 103, 86, 93, 64, 75, 34, 41, 52, 63, 14, 5, 24, 19, 202, 193, 220, 215, 230, 237, 240, 251, 146, 153, 132, 143, 190, 181, 168, 163]
VW = [0, 13, 26, 23, 52, 57, 46, 35, 104, 101, 114, 127, 92, 81, 70, 75, 208, 221, 202, 199, 228, 233, 254, 243, 184, 181, 162, 175, 140, 129, 150, 155, 187, 182, 161, 172, 143, 130, 149, 152, 211, 222, 201, 196, 231, 234, 253, 240, 107, 102, 113, 124, 95, 82, 69, 72, 3, 14, 25, 20, 55, 58, 45, 32, 109, 96, 119, 122, 89, 84, 67, 78, 5, 8, 31, 18, 49, 60, 43, 38, 189, 176, 167, 170, 137, 132, 147, 158, 213, 216, 207, 194, 225, 236, 251, 246, 214, 219, 204, 193, 226, 239, 248, 245, 190, 179, 164, 169, 138, 135, 144, 157, 6, 11, 28, 17, 50, 63, 40, 37, 110, 99, 116, 121, 90, 87, 64, 77, 218, 215, 192, 205, 238, 227, 244, 249, 178, 191, 168, 165, 134, 139, 156, 145, 10, 7, 16, 29, 62, 51, 36, 41, 98, 111, 120, 117, 86, 91, 76, 65, 97, 108, 123, 118, 85, 88, 79, 66, 9, 4, 19, 30, 61, 48, 39, 42, 177, 188, 171, 166, 133, 136, 159, 146, 217, 212, 195, 206, 237, 224, 247, 250, 183, 186, 173, 160, 131, 142, 153, 148, 223, 210, 197, 200, 235, 230, 241, 252, 103, 106, 125, 112, 83, 94, 73, 68, 15, 2, 21, 24, 59, 54, 33, 44, 12, 1, 22, 27, 56, 53, 34, 47, 100, 105, 126, 115, 80, 93, 74, 71, 220, 209, 198, 203, 232, 229, 242, 255, 180, 185, 174, 163, 128, 141, 154, 151]
WW = [0, 9, 18, 27, 36, 45, 54, 63, 72, 65, 90, 83, 108, 101, 126, 119, 144, 153, 130, 139, 180, 189, 166, 175, 216, 209, 202, 195, 252, 245, 238, 231, 59, 50, 41, 32, 31, 22, 13, 4, 115, 122, 97, 104, 87, 94, 69, 76, 171, 162, 185, 176, 143, 134, 157, 148, 227, 234, 241, 248, 199, 206, 213, 220, 118, 127, 100, 109, 82, 91, 64, 73, 62, 55, 44, 37, 26, 19, 8, 1, 230, 239, 244, 253, 194, 203, 208, 217, 174, 167, 188, 181, 138, 131, 152, 145, 77, 68, 95, 86, 105, 96, 123, 114, 5, 12, 23, 30, 33, 40, 51, 58, 221, 212, 207, 198, 249, 240, 235, 226, 149, 156, 135, 142, 177, 184, 163, 170, 236, 229, 254, 247, 200, 193, 218, 211, 164, 173, 182, 191, 128, 137, 146, 155, 124, 117, 110, 103, 88, 81, 74, 67, 52, 61, 38, 47, 16, 25, 2, 11, 215, 222, 197, 204, 243, 250, 225, 232, 159, 150, 141, 132, 187, 178, 169, 160, 71, 78, 85, 92, 99, 106, 113, 120, 15, 6, 29, 20, 43, 34, 57, 48, 154, 147, 136, 129, 190, 183, 172, 165, 210, 219, 192, 201, 246, 255, 228, 237, 10, 3, 24, 17, 46, 39, 60, 53, 66, 75, 80, 89, 102, 111, 116, 125, 161, 168, 179, 186, 133, 140, 151, 158, 233, 224, 251, 242, 205, 196, 223, 214, 49, 56, 35, 42, 21, 28, 7, 14, 121, 112, 107, 98, 93, 84, 79, 70]


class GoogleBooksDecrpyter:
    def __init__(self, key: bytes) -> None:
        self._key = key
        self._key_len = round(len(key) / 4)
        self._key_len2 = self._key_len + 6
        self._data1 = []  # Jc
        self._data2 = []  # qC
        for _ in range(4):
            self._data1.append([None, None, None, None])
            self._data2.append([None, None, None, None])
        self._data3: List[List[int]] = [None] * (4 * (self._key_len2 + 1))  # ji
        for i in range(self._key_len):
            self._data3[i] = [key[4 * i], key[4 * i + 1], key[4 * i + 2], key[4 * i + 3]]
        b = [0, 0, 0, 0]
        for i in range(self._key_len, 4 * (self._key_len2 + 1)):
            b = self._data3[i - 1].copy()
            if (i % self._key_len == 0):
                b = b[1:4] + [b[0]]
                for _ in range(4):
                    b[_] = MW[b[_]]
                t = i / self._key_len
                for _ in range(4):
                    b[_] ^= round((2 ** (t - 1) if t <= 8 else 27 * (2 ** (t - 9))) if _ % 4 == 0 else 0)
            else:
                if self._key_len > 6 and i % self._key_len == 4:
                    for _ in range(4):
                        b[_] = MW[b[_]]
            self._data3[i] = [None, None, None, None]
            for _ in range(4):
                self._data3[i][_] = self._data3[i - self._key_len][_] ^ b[_]

    def decrypt(self, data: bytes):
        first_xor = data[:16]
        le = int.from_bytes(data[16:20], 'little')
        re = b''
        data = data[20:]
        while len(re) < len(data):
            a = len(re)
            xor = list(data[a - 16:a] if a > 0 else first_xor)
            for i in range(a, min(a + 1024, len(data)), 16):
                b = data[i : i+16]
                r = self.__decrypt(b)
                for _ in range(16):
                    re += (xor[_] ^ r[_]).to_bytes(1, 'little')
                xor = list(b)
        re = re[:le]
        return re

    def __decrypt(self, a: bytes):
        for i in range(4):  # JW(this, a)
            for j in range(4):
                self._data1[i][j] = a[4 * j + i]
        self.KW(self._key_len2)  # KW(this, this.Sw);
        for i in range(1, self._key_len2):
            self.RW()  # RW(this);
            self.LW(SW)  # LW(this, SW);
            self.KW(self._key_len2 - i)  # KW(this, this.Sw - a)
            for j in range(4):
                c = self._data2[0]
                for _ in range(4):
                    c[_] = self._data1[_][j]
                self._data1[0][j] = TW[c[0]] ^ UW[c[1]] ^ VW[c[2]] ^ WW[c[3]]
                self._data1[1][j] = WW[c[0]] ^ TW[c[1]] ^ UW[c[2]] ^ VW[c[3]]
                self._data1[2][j] = VW[c[0]] ^ WW[c[1]] ^ TW[c[2]] ^ UW[c[3]]
                self._data1[3][j] = UW[c[0]] ^ VW[c[1]] ^ WW[c[2]] ^ TW[c[3]]
        self.RW()
        self.LW(SW)
        self.KW(0)
        return self.QW()

    def KW(self, l):
        for i in range(4):
            for j in range(4):
                self._data1[i][j] ^= self._data3[4 * l + j][i]

    def RW(self):
        for i in range(1, 4):
            for j in range(4):
                self._data2[i][(i + j) % 4] = self._data1[i][j]
        for i in range(1, 4):
            for j in range(4):
                self._data1[i][j] = self._data2[i][j]

    def LW(self, b: List[int]):
        for i in range(4):
            for j in range(4):
                self._data1[i][j] = b[self._data1[i][j]]

    def QW(self):
        r = [None] * 16
        for i in range(4):
            for j in range(4):
                r[j * 4 +i] = self._data1[i][j]
        return r


def decode_key(key: str) -> bytes:
    print(key)
    key = b64decode(key)
    print(key)
    key = KEY_REG.findall(key)
    print(key)
    if key is None or len(key) != 128:
        raise ValueError('Invaild key')
    r = ''
    for i in key:
        r += '1' if i[i[-1] - 48] == i[len(i) - 2] else '0'
    r = r[64:] + r[:64]
    return int(r[::-1], 2).to_bytes(16, 'little')


class MetadataParser(HTMLParser):
    def __init__(self, *k, convert_charrefs: bool = ...) -> None:
        self._metadata = ''
        self._in_script = False
        self._is_meta = False
        self._key = ''
        super().__init__(*k, convert_charrefs=convert_charrefs)

    def handle_data(self, data: str) -> None:
        if self._in_script and (self._is_meta or (self._metadata == '' and data.startswith('start'))):
            self._is_meta = True
            self._metadata += data

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag == 'script':
            self._in_script = True
        elif tag == 'img':
            for i in attrs:
                if i[0] == 'src':
                    if i[1].startswith('data:image/gif;base64,'):
                        self._key = i[1].lstrip('data:image/gif;base64,')

    def handle_endtag(self, tag: str) -> None:
        if tag == 'script':
            self._in_script = False
            self._is_meta = False

    @property
    def metadata(self) -> Optional[str]:
        if self._metadata == '':
            return None
        if self._metadata.endswith(';'):
            self._metadata = self._metadata[:-1]
        v = "function(){return [" + self._metadata[6:-1] + "]}"
        f = eval_js(v)
        return f()


cookies = MozillaCookieJar('google.txt')
cookies.load()
ses = Session()
ses.headers['user-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'
ses.headers['accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
ses.cookies = cookies
arg = ArgumentParser(description='Download from Google Play Books', add_help=True, formatter_class=RawTextHelpFormatter)
arg.add_argument('id', help=wrap("Book's id or url. Id is recommend because url may not be detected."))
arg.add_argument('-o', '--output', help=wrap('Specify the location of output file. By default it will output to current directory and use "<author> - <title>" as file name.'), metavar='FILE', dest='output')
arg.add_argument('type', help="Specify output type. (Default: null)\nSupported value:\nnull: Only download segments and resources.\nCBZ: Package all images file as a comic book ZIP archive.", nargs='?', default='null', choices=['null', 'CBZ'], metavar='type')
arg.add_argument('-c', '--cookies', help=wrap('Specify the location of cookies file. File must be Netscape HTTP Cookie File. (Default: google.txt)'), default="google.txt", metavar='FILE', dest='cookies')
arg.add_argument('-a', '--authuser', help=wrap('Specify the index of current user. Will be useful when multiply Google Account is logined in a same cookie file. Index is start at 0. (Default: 0)'), default=0, type=int, metavar='INDEX', dest='authuser')
arg.add_argument('-d', '--cache-dir', help=wrap('Specify the cache directory. By default, it will be "<author> - <title>"'), metavar='DIR', dest='cache_dir')
args = arg.parse_intermixed_args()
print(args)
try:
    re = ses.get(f"https://play.google.com/books?authuser={args.authuser}")
    if re.status_code >= 400:
        raise ValueError('Can not switch content')
    if args.id.find("://") > -1:
        arg_id_qs = parse_qs(urlparse(args.id).query)
        if 'id' in arg_id_qs:
            book_id = arg_id_qs['id'][0]
    else:
        book_id = args.id
    re = ses.get(f'https://play.google.com/books/reader?id={book_id}')
    print(re.status_code)
    print(re.reason)
    parser = MetadataParser()
    parser.feed(re.text)
    meta = parser.metadata
    if 2 not in meta[0]['available_mode']:
        raise NotImplementedError('The old version is not supported now.')
    metadata = meta[0]['metadata']
    title = metadata['title']
    num_pages = metadata['num_pages']
    authors = metadata['authors']
    pub_date = metadata['pub_date']
    publisher = metadata['publisher']
    volume_id = metadata['volume_id']
    print(title)
    print(num_pages)
    if args.cache_dir is None:
        filename = f"{authors} - {title}"
    else:
        filename = args.cache_dir
    makedirs(filename, exist_ok=True)
    makedirs('temp', exist_ok=True)
    key_file = join(filename, "encrypt.key")
    if parser._key != '' and not exists(key_file):
        keys = decode_key(parser._key)
        decrypter = GoogleBooksDecrpyter(keys)
        with open(key_file, "wb") as f:
            f.write(keys)
    elif exists(key_file):
        with open(key_file, 'rb') as f:
            decrypter = GoogleBooksDecrpyter(f.read())
    else:
        decrypter = None
    segment = meta[0]['segment']
    resources = {}
    resource_file = join(filename, "resources.json")
    if exists(resource_file):
        with open(resource_file, 'r', encoding='UTF-8') as f:
            resources = load(f)
    for i in segment:
        segment_info_file = join(filename, f"{i['label']}.json")
        if not exists(segment_info_file):
            for _ in range(3):
                try:
                    print(f"Downloading segment information: {i['label']}")
                    link = urljoin('https://play.google.com', i['link'])
                    re = ses.get(link)
                    if re.status_code >= 400:
                        raise ValueError(f'{re.status_code} {re.reason}')
                    break
                except Exception:
                    print_exc()
                    print(f'Download failed. Retry the {_ + 1} times.')
            segment = re.json()
            if segment['content_encrypted'] and 'content' in segment and decrypter is not None:
                segment['content'] = decrypter.decrypt(b64decode(segment['content'])).decode()
                segment['content_encrypted'] = False
            with open(segment_info_file, 'w', encoding='UTF-8') as f:
                dump(segment, f, ensure_ascii=False, separators=(',', ':'))
        else:
            with open(segment_info_file, 'r', encoding='UTF-8') as f:
                segment = load(f)
        if 'resource' in segment:
            for res in segment['resource']:
                res_name = ''
                res_par = parse_qs(urlparse(res['url']).query)
                if 'pg' in res_par:
                    res_name = res_par['pg'][0]
                elif 'start' in res_par:
                    res_name = res_par['start'][0]
                elif 'aid' in res_par:
                    res_name = res_par['aid'][0]
                if res_name == '':
                    raise ValueError(f"Can not detect the resource's name：{res['url']}")
                res_ext = ''
                if 'mime_type' in res:
                    if res['mime_type'] == 'image':
                        res_ext = '.jpg'
                    elif res['mime_type'] == 'text/css':
                        res_ext = '.css'
                    elif res['mime_type'] == 'video':
                        res_ext = '.mp4'
                if res_ext == '':
                    raise ValueError(f"Can not detect the resource's type：{res['mime_type']}")
                res_file = join(filename, f"{res_name}{res_ext}")
                if exists(res_file) and res['url'] in resources:
                    print(f'Skip downloading resource file：{res_file}')
                else:
                    if exists(res_file):
                        i = 1
                        res_file = join(filename, f"{res_name}_{i}{res_ext}")
                        if exists(res_file):
                            i += 1
                            res_file = join(filename, f"{res_name}_{i}{res_ext}")
                    for _ in range(3):
                        try:
                            print(f"Downloading resource file: {res_file}")
                            link = urljoin('https://play.google.com', res['url'])
                            re = ses.get(link)
                            if re.status_code >= 400:
                                raise ValueError(f'{re.status_code} {re.reason}')
                            break
                        except Exception:
                            print_exc()
                            print(f'Download failed. Retry the {_ + 1} times.')
                    if res_ext == '.jpg':
                        with open(res_file, 'wb') as f:
                            f.write(re.content)
                    elif res_ext == '.css':
                        res_css = re.json()
                        with open(res_file, 'w', encoding='UTF-8') as f:
                            f.write(res_css['style'])
                    elif res_ext == '.mp4':
                        video_info = parse_qs(re.text)
                        if video_info['status'][0] != 'ok':
                            raise ValueError('Can not parse video')
                        fmt_list = video_info['fmt_list'][0].split(',')
                        ind = 1
                        for info in fmt_list:
                            info = info.split('/')
                            print(f'{ind}: ID: {info[0]} Video size: {info[1]}')
                            ind += 1
                        choice = input('Please choose：')
                        while not choice.isnumeric() or int(choice) == 0 or int(choice) >= ind:
                            choice = input('Please choose：')
                        fmt = fmt_list[int(choice) - 1]
                        fmt_id = fmt.split('/')[0]
                        fmt_stream_map = video_info['fmt_stream_map'][0].split(',')
                        for fmt_stream in fmt_stream_map:
                            fmt_stream = fmt_stream.split('|')
                            if fmt_stream[0] == fmt_id:
                                link = fmt_stream[1]
                        for _ in range(3):
                            try:
                                print(f'Downloading video file：{res_file}')
                                re = ses.get(link, stream=True)
                                if re.status_code >= 400:
                                    raise ValueError(f'{re.status_code} {re.reason}')
                                with open(res_file, 'wb') as f:
                                    for i in re.iter_content(1024):
                                        if i:
                                            f.write(i)
                                break
                            except Exception:
                                print_exc()
                                print(f'Download failed. Retry the {_ + 1} times.')
                                if exists(res_file):
                                    remove(res_file)
                    nres = res.copy()
                    del nres['url']
                    nres['file'] = res_file
                    resources[res['url']] = nres
    if args.type == 'CBZ':
        if 'resource' in segment:
            output = args.output if args.output else f'{authors} - {title}.cbz'
            z = ZipFile(output, 'w', ZIP_STORED, True)
            for segment in meta[0]['segment']:
                segment_info_file = join(filename, f"{segment['label']}.json")
                with open(segment_info_file, 'r', encoding='UTF-8') as f:
                    segment = load(f)
                for res in segment['resource']:
                    nres = resources[res['url']]
                    if 'mime_type' in nres and nres['mime_type'] == 'image':
                        print(f"Add {nres['file']} to commic book archive.")
                        z.write(nres['file'], relpath(nres['file'], filename))
finally:
    cookies.save()
    try:
        with open(resource_file, 'w', encoding='UTF-8') as f:
            dump(resources, f, ensure_ascii=False, separators=(',', ':'))
    except Exception:
        pass
