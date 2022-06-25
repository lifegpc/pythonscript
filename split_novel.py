from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from re import compile
from os.path import join, splitext
from os import makedirs


arg = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
arg.add_argument('PATH', help='The path to input file.')
arg.add_argument('-o', '--output', help="The path to output directory.",
                 metavar='OUTPUT', dest='output')
arg.add_argument('-e', '--encoding', help='File encoding.',
                 default='UTF-8', metavar='ENCODING', dest='encoding')
arg.add_argument('-r', '--regex', help='Chapter detect regex.',
                 default=r'^第 ?\d+ ?章', metavar='REGEX', dest='regex')
args = arg.parse_intermixed_args()
print(args)
regex = compile(args.regex)
if args.output is None:
    args.output = splitext(args.PATH)[0]
makedirs(args.output, exist_ok=True)
cur = []
ind = 1
with open(args.PATH, 'r', encoding=args.encoding) as f:
    while True:
        now = f.readline()
        if not now.endswith('\n'):
            break
        now = now.rstrip('\n')
        if regex.search(now) is not None:
            print(now, len(cur))
            if len(cur):
                with open(join(args.output, f'{ind:06}.txt'), 'w', encoding=args.encoding) as o:
                    o.write('\n'.join(cur))
                    cur = []
                    ind += 1
        cur.append(now)
if len(cur):
    with open(join(args.output, f'{ind:06}.txt'), 'w', encoding=args.encoding) as o:
        o.write('\n'.join(cur))
        cur = []
        ind += 1
