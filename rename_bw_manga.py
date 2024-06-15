from argparse import ArgumentParser
from json import loads
from os import listdir
from os.path import exists, isdir, join, splitext
from shutil import move
from typing import List
from zipfile import ZipFile


p = ArgumentParser()
p.add_argument("-r", "--recursive", help="Recursively process input directory",
               action='store_true', default=False)
p.add_argument("-v", "--verbose", help="Enable verbose logging",
               action='store_true', default=False)
p.add_argument("input", help="Input file/directory.", default='.', nargs='?')


def get_zip_files(dir: str, r: bool) -> List[str]:
    if not isdir(dir):
        if exists(dir) and dir.endswith('.zip'):
            return [dir]
        return []
    files = listdir(dir)
    re = []
    for file in files:
        file = join(dir, file)
        if isdir(file):
            if r:
                re += get_zip_files(file, r)
        elif file.endswith('.zip'):
            re.append(file)
    return re


def rename_zip(file: str, json_path: str, verbose: bool):
    tmp = splitext(file)
    tmp_file = tmp[0] + '_tmp' + tmp[1]
    with ZipFile(file, 'r') as inp:
        files = inp.namelist()
        json_data = inp.open("configuration_pack.json")
        if not json_data:
            raise ValueError('Can not find configuration_pack.json in zip.')
        files.remove("configuration_pack.json")
        json_data = json_data.read()
        with open(json_path, 'wb') as json:
            json.write(json_data)
        if verbose:
            print(f'{file}/configuration_pack.json -> {json_path}')
        data = loads(json_data)
        config = data['configuration']
        with ZipFile(tmp_file, 'w') as out:
            clen = len(str(len(config['contents'])))
            for c in config['contents']:
                f = c['file']
                fc = data[f]
                plen = len(str(len(fc['FileLinkInfo']['PageLinkInfoList'])))
                for page in fc['FileLinkInfo']['PageLinkInfoList']:
                    page_no = page['Page']['No']
                    page_src = f"{f}/{page_no}.{c['type']}"
                    page_dest = f"{str(c['index']).rjust(clen, '0')}_{f.replace('/', '_')}_{str(page_no).rjust(plen, '0')}.{c['type']}"  # noqa: E501
                    page_data = inp.open(page_src)
                    if not page_data:
                        raise ValueError(f'Can not find {page_src}')
                    files.remove(page_src)
                    out.writestr(page_dest, page_data.read())
                    if verbose:
                        print(f'{file}/{page_src} -> {tmp_file}/{page_dest}')
    files = [f for f in files if not f.endswith('/')]
    if len(files) > 0:
        print(files)
        raise ValueError('Some file not used.')
    move(tmp_file, file)
    if verbose:
        print(f'{tmp_file} -> {file}')


arg = p.parse_intermixed_args()
for file in get_zip_files(arg.input, arg.recursive):
    json_path = splitext(file)[0] + '.json'
    if exists(json_path):
        if arg.verbose:
            print(f'Skip file {file}.')
        continue
    rename_zip(file, json_path, arg.verbose)
