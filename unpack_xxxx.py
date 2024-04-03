from argparse import ArgumentParser
from json import load, dump
import os
from os.path import splitext, join
import xxtea


def try_decode(fn: str):
    with open(fn, 'rb') as f:
        data = f.read(6)
        if data != b'jiaile':
            return
        data = f.read()
    data = xxtea.decrypt(data, b"6uJL0SF5CQQuPZoW", padding=False)
    with open(fn, 'wb') as f:
        f.write(data)
    print(f"Decrypted {fn}")

def remove_unneed(fn: str):
    with open(fn, 'r', encoding='utf-8') as f:
        data = load(f)
    re = []
    for i in data['FileReferences']['Textures']:
        if i.endswith(".pvr.ccz"):
            re.append(i[0:-8] + '.png')
        else:
            re.append(i)
    data['FileReferences']['Textures'] = re
    with open(fn, 'w', encoding='utf-8') as f:
        dump(data, f)
    print('Removed unneeded files from', fn)

ap = ArgumentParser()
ap.add_argument('DIR', help='Input Directory')
args = ap.parse_args()
for (root, dirname, filename) in os.walk(args.DIR[0]):
    for fn in filename:
        ext = splitext(fn)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png']:
            try_decode(join(root, fn))
        elif fn.endswith('.model3.json'):
            remove_unneed(join(root, fn))
        elif fn.endswith('.pvr.ccz'):
            os.remove(join(root, fn))
            print('Removed', fn)
