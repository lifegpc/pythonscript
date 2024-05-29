from argparse import ArgumentParser
from os import listdir, link, symlink
from os.path import join, split


def get_files(input: str):
    d = split(input)
    name = d[1]
    d = d[0]
    re = []
    for i in listdir(d):
        if i.startswith(f"{name}."):
            re.append(join(d, i))
    return re


p = ArgumentParser()
p.add_argument("INPUT", help='input')
p.add_argument("OUTPUT", help='output')
p.add_argument("-H", "--hardlink", action="store_true", default=False)


def main(args=None):
    arg = p.parse_args(args)
    outd = split(arg.OUTPUT)
    outname = outd[1] + "."
    outd = outd[0]
    inpname = split(arg.INPUT)[1] + "."
    for f in get_files(arg.INPUT):
        target = join(outd, split(f)[1].replace(inpname, outname))
        if arg.hardlink:
            link(f, target)
        else:
            symlink(f, target)
        print(target, ' -> ', f)


if __name__ == "__main__":
    main()
