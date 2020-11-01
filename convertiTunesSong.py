# convertiTunesSong.py
# v0.0.1
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
from xml.sax import make_parser, ContentHandler
from xml.sax.handler import feature_namespaces
from base64 import decodebytes
from time import strptime, strftime, localtime
from os.path import exists, splitext, basename, dirname
from regex import search
from urllib.parse import unquote_plus


class InvalidiTunesXMLException(Exception):
    def __init__(self, s=None):
        if s is None:
            Exception.__init__("Invalid iTunes XML.")
        else:
            Exception.__init__(f"Invalid iTunes XML: {s}")


class iTunesContentHandler(ContentHandler):
    data = None
    dictlist = []
    i = -1
    key = ""
    tempc = ""
    dic = None
    hasd = False
    dit = 0

    def startElement(self, tag, attributes):
        if tag == "dict":
            if self.i == -1:
                self.data = {}
                self.dic = self.data
                self.dictlist.append(self.data)
            else:
                if isinstance(self.dic, dict):
                    self.dic[self.key] = {}
                    self.dic = self.dic[self.key]
                else:
                    t = {}
                    self.dic.append(t)
                    self.dic = t
                self.dictlist.append(self.dic)
            self.i = self.i + 1
        elif tag == "array":
            if self.i == -1:
                raise InvalidiTunesXMLException()
            else:
                if isinstance(self.dic, dict):
                    self.dic[self.key] = []
                    self.dic = self.dic[self.key]
                else:
                    t = []
                    self.dic.append(t)
                    self.dic = t
                self.dictlist.append(self.dic)
            self.i = self.i + 1
        elif tag in ['plist', 'key', 'string', 'data', 'date', 'true', 'false', 'real', 'integer']:
            pass
        else:
            raise InvalidiTunesXMLException(f"Unknown tag: {tag}")
        if tag != "plist" and tag != "dict" and tag != "array":
            self.hasd = True

    def characters(self, context):
        if self.hasd:
            self.tempc = self.tempc + context

    def endElement(self, tag):
        if tag == "dict" or tag == "array":
            self.i = self.i - 1
            if self.i != -1:
                self.dictlist.remove(self.dic)
                self.dic = self.dictlist[self.i]
        elif tag == 'key':
            self.key = self.tempc
        elif tag == 'string':
            if isinstance(self.dic, dict):
                self.dic[self.key] = self.tempc
            else:
                self.dic.append(self.tempc)
        elif tag == "data":
            b = decodebytes(self.tempc.encode())
            if isinstance(self.dic, dict):
                self.dic[self.key] = b
            else:
                self.dic.append(b)
        elif tag == 'date':
            t = strptime(self.tempc, '%Y-%m-%dT%H:%M:%SZ')
            if isinstance(self.dic, dict):
                self.dic[self.key] = t
            else:
                self.dic.append(t)
        elif tag == "true":
            if isinstance(self.dic, dict):
                self.dic[self.key] = True
            else:
                self.dic.append(True)
        elif tag == "false":
            if isinstance(self.dic, dict):
                self.dic[self.key] = False
            else:
                self.dic.append(False)
        elif tag == 'real':
            f = float(self.tempc)
            if isinstance(self.dic, dict):
                self.dic[self.key] = f
            else:
                self.dic.append(f)
        elif tag == "integer":
            i = int(self.tempc)
            if isinstance(self.dic, dict):
                self.dic[self.key] = i
            else:
                self.dic.append(i)
        self.tempc = ""
        self.hasd = False


def ParserXML(fn: str):
    p = make_parser()
    p.setFeature(feature_namespaces, 0)
    h = iTunesContentHandler()
    p.setContentHandler(h)
    p.parse(fn)
    data = p.getContentHandler().data
    return data


class main():
    fn = ''  # The path of iTunes Library.xml
    sall = True  # select all?
    fmt = ''  # output file format
    ext = 'm4a'  # output flie ext
    fnt = '<Location>/<FileName>.<ext>'  # File name template
    ab = "320k"  # bitrate
    tft = '%Y-%m-%d %H:%M:%S'  # Time format template

    def __init__(self, ip: dict = {}):
        if 'fn' in ip:
            self.fn = ip['fn']
        else:
            self.fn = 'iTunes Library.xml'
        if not exists(self.fn):
            raise FileNotFoundError(self.fn)
        data = ParserXML(self.fn)
        if self.sall:
            if 'Tracks' in data:
                l: dict = self._filterList(data['Tracks'])
                for key in l.keys():
                    d = l[key]
                    fn = self._getFileName(d)
                    print(fn)

    def _filterList(self, li: dict):
        l = {}
        for key in li.keys():
            d = li[key]
            if (not 'Protected' in d or not d['Protected']) and d['Track Type'] == "File":
                l[key] = d
        return l

    def _getFileName(self, data: dict):
        un = 'Unknown'
        reg = r'[\\]?<([^>]*)>'
        reg4 = r'[^[:print:]/\\:\*\?\"<>\|]'
        fn = self.fnt
        ns = search(reg, fn)
        while ns is not None:
            ma = ns.group()
            if ma[0] == '\\':
                pos = ns.end()
                ns = search(reg, fn, pos=pos)
                continue
            le = 0
            for i in range(len(ma)):
                if i > 0 and ma[i-1] == '\\':
                    continue
                if ma[i] == '<':
                    le = le + 1
                if ma[i] == '>':
                    le = le - 1
            pos = ns.end()
            while le > 0:
                ma = ma + fn[pos]
                pos = pos + 1
                i = i + 1
                if ma[-2] == '\\':
                    continue
                if ma[i] == '<':
                    le = le + 1
                if ma[i] == '>':
                    le = le - 1
            if ma[-2] == '\\':
                pos = ns.end()
                ns = search(reg, fn, pos=pos)
                continue
            ke = ma[1:-1]
            unf = True
            if ke[0] == '?':
                unf = False
                if len(ke) > 1:
                    ke = ke[1:]
                else:
                    pos = ns.end()
                    ns = search(reg, fn, pos=pos)
                    continue
            at = ""
            at3 = ""
            if ke[0] == '(':
                at = "("
                le = 1
                i = 1
                while le > 0:
                    at = at + ke[i]
                    i = i + 1
                    if at[-2] == '\\':
                        continue
                    if at[-1] == '(':
                        le = le + 1
                    if at[-1] == ')':
                        le = le - 1
                ke = ke.replace(at, '', 1)
                at = at[1:-1]
                at, at3 = self._splitat(at)
            at2 = ""
            at4 = ""
            if len(ke) > 1 and ke[-1] == ')' and ke[-2] != '\\':
                at2 = ")"
                le = 1
                i = -2
                while le > 0:
                    at2 = ke[i] + at2
                    i = i - 1
                    if ke[i] == '\\':
                        continue
                    if at2[0] == '(':
                        le = le - 1
                    if at2[0] == ')':
                        le = le + 1
                ke = ke.replace(at2, '', 1)
                at2 = at2[1:-1]
                at2, at4 = self._splitat(at2)
            pos = ns.start()
            if ke == "ext":
                fn = fn.replace(ma, self.ext, 1)
            elif ke == 'Album':
                if 'Album' in data:
                    fn = fn.replace(ma, f"{at}{data['Album']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "AlbumArtist":
                if 'Album Artist' in data:
                    fn = fn.replace(ma, f"{at}{data['Album Artist']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == 'Artist':
                if 'Artist' in data:
                    fn = fn.replace(ma, f"{at}{data['Artist']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "ArtworkCount":
                if 'Artwork Count' in data:
                    fn = fn.replace(ma, f"{at}{data['Artwork Count']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "BPM":
                if 'BPM' in data:
                    fn = fn.replace(ma, f"{at}{data['BPM']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "BitRate":
                if 'Bit Rate' in data:
                    fn = fn.replace(ma, f"{at}{data['Bit Rate']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "Compilation":
                if 'Compilation' in data:
                    fn = fn.replace(ma, f"{at}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "Composer":
                if 'Composer' in data:
                    fn = fn.replace(ma, f"{at}{data['Composer']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "DateAdded":
                if 'Date Added' in data:
                    fn = fn.replace(
                        ma, f"{at}{strftime(self.tft, data['Date Added'])}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "DateModified":
                if 'Date Modified' in data:
                    fn = fn.replace(
                        ma, f"{at}{strftime(self.tft, data['Date Modified'])}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "DiscCount":
                if 'Disc Count' in data:
                    fn = fn.replace(ma, f"{at}{data['Disc Count']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "DiscNumber":
                if 'Disc Number' in data:
                    fn = fn.replace(ma, f"{at}{data['Disc Number']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "FileFolderCount":
                if 'File Folder Count' in data:
                    fn = fn.replace(
                        ma, f"{at}{data['File Folder Count']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "FileName":
                if 'Location' in data:
                    fn = fn.replace(
                        ma, f"{at}{unquote_plus(splitext(basename(data['Location']))[0])}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "Genre":
                if 'Genre' in data:
                    fn = fn.replace(ma, f"{at}{data['Genre']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "Kind":
                if 'Kind' in data:
                    fn = fn.replace(ma, f"{at}{data['Kind']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "LibraryFolderCount":
                if 'Library Folder Count' in data:
                    fn = fn.replace(
                        ma, f"{at}{data['Library Folder Count']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "Location":
                if 'Location' in data:
                    loc = unquote_plus(dirname(data['Location']))
                    if loc.startswith('file://localhost/'):
                        loc = loc[17:]
                    fn = fn.replace(ma, f"{at}{loc}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "Name":
                if 'Name' in data:
                    fn = fn.replace(ma, f"{at}{data['Name']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "PersistentID":
                if 'Persistent ID' in data:
                    fn = fn.replace(ma, f"{at}{data['Persistent ID']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "PlayCount":
                if 'Play Count' in data:
                    fn = fn.replace(ma, f"{at}{data['Play Count']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "PlayDate":
                if 'Play Date' in data:
                    fn = fn.replace(
                        ma, f"{at}{strftime(self.tft, localtime(data['Play Date']))}{at2}", 1)
                elif 'Play Date UTC' in data:
                    fn = fn.replace(
                        ma, f"{at}{strftime(self.tft, data['Play Date UTC'])}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "Purchased":
                if 'Purchased' in data and data['Purchased']:
                    fn = fn.replace(ma, f"{at}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "ReleaseDate":
                if 'Release Date' in data:
                    fn = fn.replace(
                        ma, f"{at}{strftime(self.tft, data['Release Date'])}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "SampleRate":
                if 'Sample Rate' in data:
                    fn = fn.replace(ma, f"{at}{data['Sample Rate']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "Size":
                if 'Size' in data:
                    fn = fn.replace(ma, f"{at}{data['Size']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "SkipCount":
                if 'Skip Count' in data:
                    fn = fn.replace(ma, f"{at}{data['Skip Count']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "SkipDate":
                if 'Skip Date' in data:
                    fn = fn.replace(
                        ma, f"{at}{strftime(self.tft, data['Skip Date'])}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "SortAlbum":
                if 'Sort Album' in data:
                    fn = fn.replace(ma, f"{at}{data['Sort Album']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "SortArtist":
                if 'Sort Artist' in data:
                    fn = fn.replace(ma, f"{at}{data['Sort Artist']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "SortComposer":
                if 'Sort Composer' in data:
                    fn = fn.replace(ma, f"{at}{data['Sort Composer']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "SortName":
                if 'Sort Name' in data:
                    fn = fn.replace(ma, f"{at}{data['Sort Name']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "TotalTime":
                if 'Total Time' in data:
                    fn = fn.replace(ma, f"{at}{data['Total Time']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "TrackCount":
                if 'Track Count' in data:
                    fn = fn.replace(ma, f"{at}{data['Track Count']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "TrackID":
                if 'Track ID' in data:
                    fn = fn.replace(ma, f"{at}{data['Track ID']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "TrackNumber":
                if 'Track Number' in data:
                    fn = fn.replace(ma, f"{at}{data['Track Number']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "TrackType":
                if 'Track Type' in data:
                    fn = fn.replace(ma, f"{at}{data['Track Type']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            elif ke == "Year":
                if 'Year' in data:
                    fn = fn.replace(ma, f"{at}{data['Year']}{at2}", 1)
                elif unf:
                    fn = fn.replace(ma, f"{at3}{un}{at4}", 1)
                else:
                    fn = fn.replace(ma, f'{at3}{at4}', 1)
            else:
                pos = ns.end()
            ns = search(reg, fn, pos=pos)
        fn = fn.replace('\\<', '<')
        fn = fn.replace('\\>', '>')
        fn = fn.replace('\\(', '(')
        fn = fn.replace('\\)', ')')
        rs = search(reg4, fn)
        while rs is not None:
            fn = fn.replace(rs.group(), '_')
            rs = search(reg4, fn)
        while len(fn) > 0 and fn[0] == ' ':
            fn = fn[1:]
        return fn

    def _splitat(self, s: str):
        atl = s.split('|')
        asm = [atl[0]]
        j = 0
        for i in range(1, len(atl)):
            if atl[i-1][-1] == '\\' or j == 1:
                if atl[i-1][-1] == '\\':
                    asm[j] = asm[j][:-1] + '|' + atl[i]
                else:
                    asm[j] = asm[j] + atl[i]
            else:
                j = j + 1
                asm.append(atl[i])
        if len(asm) == 1:
            return asm[0], ''
        else:
            return asm[0], asm[1]


if __name__ == "__main__":
    main()
