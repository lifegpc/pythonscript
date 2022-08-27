# comic_library_info.py
# (C) 2022 lifegpc
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
from argparse import ArgumentParser, Namespace
from json import dump as dumpjson, load as loadjson
from os import listdir
from os.path import abspath, isdir, isfile, join, relpath, split as splitpath
from os.path import splitext
from typing import Any, Callable, Dict, List, Optional, Union
import xml.etree.ElementTree as ET
from zipfile import ZipFile
try:
    from yaml import dump as dumpyaml, load as loadyaml
    try:
        from yaml import CSafeDumper as SafeDumper, CSafeLoader as SafeLoader
    except ImportError:
        from yaml import SafeDumper, SafeLoader
    have_yaml = True
except ImportError:
    have_yaml = False

argp = ArgumentParser(description="A tool to scan/modify comic's info.")
argp.add_argument('-V', '--version', action='version', version="%(prog)s 1.0.0")  # noqa: E501
argp.add_argument('-v', '--verbose', action='count', help='Enable verbose output.', default=0)  # noqa: E501
argp.add_argument('ACTION', choices=['d', 'dump', 'm', 'modify'], help='d/dump Dump the file which contains info. m/modify Use informaiton from file to modify comic\'s information.')  # noqa: E501
argp.add_argument('PATH', action='append', nargs='*', help='The path to the library you want to scan.')  # noqa: E501
argp.add_argument('-f', '--file', help='The location of the file which contains comic info.')  # noqa: E501
argp.add_argument('-t', '--type', help='The type of the file which contains comic info.', choices=['json', 'yaml'])  # noqa: E501
argp.add_argument('-b', '--base', help='The base directory.')


def guess_type_from_file_name(fn: str) -> Optional[str]:
    ext = splitext(fn)[1]
    if ext in ['.yaml', '.yml']:
        return 'yaml'
    if ext in ['.json', '.jsonc']:
        return 'json'


def guess_type(path: str) -> Optional[str]:
    ext = splitext(path)[1]
    if ext in ['.cbz']:
        return 'cbz'


def split_path(path: str) -> List[str]:
    path_list = []
    tmp = ''
    for i in path:
        if i in ['/', '\\']:
            if tmp == '':
                continue
            else:
                if tmp != '.':
                    path_list.append(tmp)
                tmp = ''
        else:
            tmp += i
    if tmp not in ['.', '']:
        path_list.append(tmp)
    return path_list


def extract_str(ele: ET.Element) -> str:
    return '' if ele.text is None else ele.text


def extract_xml_content(ele: ET.Element, key: str, obj: Dict[str, Any],
                        callback: Callable[[ET.Element],
                                           Optional[Any]]) -> bool:
    try:
        e = ele.find(key)
        if e is None:
            return False
        data = callback(e)
        if data is not None:
            obj[key] = data
        return True
    except Exception:
        return False


def extract_xml_attrs(ele: ET.Element, key: str, obj: Dict[str, Any],
                      callback: Callable[[str], Optional[Any]]) -> bool:
    try:
        if key not in ele.attrib:
            return False
        v = ele.attrib[key]
        data = callback(v)
        if data is not None:
            obj[key] = data
        return True
    except Exception:
        return False


def filter_int(s: str) -> Optional[int]:
    try:
        return int(s)
    except Exception:
        pass


def extract_int(ele: ET.Element) -> Optional[int]:
    s = extract_str(ele)
    return filter_int(s)


def filter_manga(s: str) -> Optional[str]:
    s = s.lower()
    if s == 'unknown':
        return 'Unknown'
    if s == 'yes':
        return 'Yes'
    if s == 'no':
        return 'No'
    if s == 'yesandrighttoleft':
        return 'YesAndRightToLeft'


def extract_manga(ele: ET.Element) -> Optional[str]:
    e = extract_str(ele)
    return filter_manga(e)


def filter_yesno(s: str) -> Optional[bool]:
    s = s.lower()
    if s == "yes":
        return True
    elif s == "no":
        return False


def extract_yesno(ele: ET.Element) -> Optional[bool]:
    s = extract_str(ele)
    return filter_yesno(s)


def filter_age_rating(s: str) -> Optional[str]:
    s = s.lower()
    if s == 'unknown':
        return 'Unknown'
    if s == 'adults only 18+':
        return 'Adults Only 18+'
    if s == 'early childhood':
        return 'Early Childhood'
    if s == 'everyone':
        return 'Everyone'
    if s == 'everyone 10+':
        return 'Everyone 10+'
    if s == 'g':
        return 'G'
    if s == 'kids to adults':
        return 'Kids to Adults'
    if s == 'm':
        return 'M'
    if s == 'ma15+':
        return 'MA15+'
    if s == 'mature 17+':
        return 'Mature 17+'
    if s == 'pg':
        return 'PG'
    if s == 'r18+':
        return 'R18+'
    if s == 'rating pending':
        return 'Rating Pending'
    if s == 'teen':
        return 'Teen'
    if s == 'x18+':
        return 'X18+'


def extract_age_rating(ele: ET.Element) -> Optional[str]:
    e = extract_str(ele)
    return filter_age_rating(e)


def filter_comic_page_type(i: str) -> Optional[str]:
    i = i.lower()
    if i == 'frontcover':
        return 'FrontCover'
    elif i == 'innercover':
        return 'InnerCover'
    elif i == 'roundup':
        return 'Roundup'
    elif i == 'story':
        return 'Story'
    elif i == 'advertisement':
        return 'Advertisement'
    elif i == 'editorial':
        return 'Editorial'
    elif i == 'letters':
        return 'Letters'
    elif i == 'preview':
        return 'Preview'
    elif i == 'backCover':
        return 'BackCover'
    elif i == 'other':
        return 'Other'
    elif i == 'deleted':
        return 'Deleted'


def extract_comic_page_type(s: str) -> List[str]:
    types = []
    for i in s.split(' '):
        i = filter_comic_page_type(i)
        if i is not None:
            types.append(i)
    return types


def filter_bool(s: str) -> Optional[bool]:
    s = s.lower()
    if s == 'true':
        return True
    if s == 'false':
        return False


def extract_bool(ele: ET.Element) -> Optional[bool]:
    s = extract_str(ele)
    return filter_bool(s)


def extract_comic_page_info(ele: ET.Element) -> Optional[Dict[str, Any]]:
    obj = {}
    if not extract_xml_attrs(ele, "Image", obj, filter_int):
        return False
    extract_xml_attrs(ele, "Story", obj, extract_comic_page_type)
    extract_xml_attrs(ele, "DoublePage", obj, filter_bool)
    extract_xml_attrs(ele, "ImageSize", obj, filter_int)
    extract_xml_attrs(ele, "Key", obj, lambda s: s)
    extract_xml_attrs(ele, "Bookmark", obj, lambda s: s)
    extract_xml_attrs(ele, "ImageWidth", obj, filter_int)
    extract_xml_attrs(ele, "ImageHeight", obj, filter_int)
    return obj


def extract_array_of_comic_page_info(ele: ET.Element) -> List[Dict[str, Any]]:
    pages = []
    childrens = ele.getchildren()
    for i in childrens:
        if i.tag == 'Page':
            dat = extract_comic_page_info(i)
            if dat is not None:
                pages.append(dat)
    return pages


def filter_rating(s) -> Optional[float]:
    try:
        f = float(s)
        f = round(f, 1)
        return f if f >= 0 and f <= 5 else None
    except Exception:
        pass


def extract_rating(ele: ET.Element) -> Optional[float]:
    s = extract_str(ele)
    return filter_rating(s)


def parse_xml(content: Union[str, bytes]) -> Optional[Dict[str, Any]]:
    try:
        root = ET.fromstring(content)
    except Exception:
        return None
    obj = {}
    extract_xml_content(root, "Title", obj, extract_str)
    extract_xml_content(root, "Series", obj, extract_str)
    extract_xml_content(root, "Number", obj, extract_str)
    extract_xml_content(root, "Count", obj, extract_int)
    extract_xml_content(root, "Volume", obj, extract_int)
    extract_xml_content(root, "AlternateSeries", obj, extract_str)
    extract_xml_content(root, "AlternateNumber", obj, extract_str)
    extract_xml_content(root, "AlternateCount", obj, extract_int)
    extract_xml_content(root, "Summary", obj, extract_str)
    extract_xml_content(root, "Notes", obj, extract_str)
    extract_xml_content(root, "Year", obj, extract_int)
    extract_xml_content(root, "Month", obj, extract_int)
    extract_xml_content(root, "Day", obj, extract_int)
    extract_xml_content(root, "Writer", obj, extract_str)
    extract_xml_content(root, "Penciller", obj, extract_str)
    extract_xml_content(root, "Inker", obj, extract_str)
    extract_xml_content(root, "Colorist", obj, extract_str)
    extract_xml_content(root, "Letterer", obj, extract_str)
    extract_xml_content(root, "CoverArtist", obj, extract_str)
    extract_xml_content(root, "Editor", obj, extract_str)
    extract_xml_content(root, "Translator", obj, extract_str)
    extract_xml_content(root, "Publisher", obj, extract_str)
    extract_xml_content(root, "Imprint", obj, extract_str)
    extract_xml_content(root, "Genre", obj, extract_str)
    extract_xml_content(root, "Tags", obj, extract_str)
    extract_xml_content(root, "Web", obj, extract_str)
    extract_xml_content(root, "PageCount", obj, extract_int)
    extract_xml_content(root, "LanguageISO", obj, extract_str)
    extract_xml_content(root, "Format", obj, extract_str)
    extract_xml_content(root, "BlackAndWhite", obj, extract_yesno)
    extract_xml_content(root, "Manga", obj, extract_manga)
    extract_xml_content(root, "Characters", obj, extract_str)
    extract_xml_content(root, "Teams", obj, extract_str)
    extract_xml_content(root, "Locations", obj, extract_str)
    extract_xml_content(root, "ScanInformation", obj, extract_str)
    extract_xml_content(root, "StoryArc", obj, extract_str)
    extract_xml_content(root, "StoryArcNumber", obj, extract_str)
    extract_xml_content(root, "SeriesGroup", obj, extract_str)
    extract_xml_content(root, "AgeRating", obj, extract_age_rating)
    extract_xml_content(root, "Pages", obj, extract_array_of_comic_page_info)
    extract_xml_content(root, "CommunityRating", obj, extract_rating)
    return obj


def iter_path(args: Namespace, path: str, data: object):
    rpath = relpath(path, args.base)
    path_list = split_path(rpath)
    if args.verbose > 2:
        print(f'Split {rpath} to {path_list}')
    tdata = data
    for p in path_list:
        if p not in tdata:
            if args.ACTION in ['d', 'dump']:
                tdata[p] = {'type': 'directory', 'tree': {}}
            else:
                tdata[p]
        tdata = tdata[p]['tree']
    for f in listdir(path):
        fpath = join(path, f)
        rfpath = relpath(fpath, args.base)
        if args.verbose > 0:
            print(f'Scan {rfpath}')
        if isdir(fpath):
            iter_path(args, fpath, data)
        elif isfile(fpath):
            fn = splitpath(fpath)[1]
            typ = guess_type(fn)
            if args.verbose > 2:
                print(f'Guess type: {typ}')
            if typ == 'cbz':
                tdata[fn] = {'type': 'cbz', 'comic_info': None}
                if args.ACTION in ['d', 'dump']:
                    with ZipFile(fpath, 'r', allowZip64=True) as z:
                        if args.verbose > 1:
                            print(f"Opened {rfpath}.")
                        try:
                            info = z.getinfo("ComicInfo.xml")
                            if args.verbose > 2:
                                print(f"ComicInfo.xml information: {info}")
                        except KeyError:
                            info = None
                        if info is not None:
                            try:
                                content = z.read(info)
                                if args.verbose > 1:
                                    print(f"Opend ComicInfo.xml in {rfpath}")
                                if args.verbose > 3:
                                    print("ComicInfo.xml Content:")
                                    try:
                                        content2 = content.decode('UTF-8')
                                    except Exception:
                                        content2 = content
                                    print(content2)
                                info = parse_xml(content)
                                tdata[fn]['comic_info'] = info
                            except Exception:
                                pass
            else:
                tdata[fn] = {'type': 'file'}
        else:
            print(f'{rfpath}({fpath}) has unknown file type.')


def run(args: Optional[List[str]] = None):
    args = argp.parse_args(args)
    args.PATH = args.PATH[0]
    if args.file is None:
        args.file = 'comic_info.json'
    if args.type is None:
        args.type = guess_type_from_file_name(args.file)
        if args.type is None:
            raise ValueError('Failed to guess file type.')
    if args.ACTION in ['d', 'dump'] and len(args.PATH) == 0:
        args.PATH.append('.')
    if args.ACTION in ['d', 'dump'] and args.base is None:
        args.base = abspath('.')
    if args.type == 'yaml' and not have_yaml:
        raise ValueError('pyyaml not installed but can be installed with pip install pyyaml.')  # noqa: E501
    if args.verbose > 1:
        print(args)
    if args.ACTION in ['d', 'dump']:
        args.base = abspath(args.base)
        data = {'path': [], 'base': args.base, 'tree': {}}
        for p in args.PATH:
            data['path'].append(relpath(abspath(p), args.base))
    elif args.ACTION in ['m', 'modify']:
        if args.type == 'json':
            with open(args.file, 'r', encoding='UTF-8') as f:
                data = loadjson(f)
        elif args.type == 'yaml':
            with open(args.file, 'r', encoding='UTF-8') as f:
                data = loadyaml(f, SafeLoader)
        if args.PATH is None:
            for p in data['path']:
                args.PATH.append(join(args.base, p))
        if args.base is None:
            args.base = data['base']
        else:
            args.base = abspath(args.base)
    if args.verbose > 2:
        print(data)
    for p in args.PATH:
        iter_path(args, abspath(p), data['tree'])
    if args.ACTION in ['d', 'dump']:
        if args.type == 'json':
            with open(args.file, 'w', encoding='UTF-8') as f:
                dumpjson(data, f, ensure_ascii=False, separators=(',', ':'))
        elif args.type == 'yaml':
            with open(args.file, 'w', encoding='UTF-8') as f:
                dumpyaml(data, f, SafeDumper, allow_unicode=True)


if __name__ == "__main__":
    run()
