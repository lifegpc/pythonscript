from argparse import ArgumentParser
from os.path import exists, isdir, join
from os import makedirs, listdir, link


p = ArgumentParser(description='Link files in a directory to another directory.')  # noqa: E501
p.add_argument('-a', '--all', help='Include all files.', action='store_true')  # noqa: E501
p.add_argument('input', help='The path to the input directory.')
p.add_argument('output', help='The path to the output directory.')


def hardlink_files(input: str, output: str, all: bool):
    if exists(input) and not isdir(input):
        raise ValueError(f"{input} is not a directory.")
    if exists(output) and not isdir(output):
        raise ValueError(f"{output} is not a directory.")
    if not exists(output):
        makedirs(output)
    for f in listdir(input):
        if not all and f.startswith('.'):
            continue
        src = join(input, f)
        dst = join(output, f)
        if isdir(src):
            hardlink_files(src, dst, all)
            continue
        if exists(dst):
            print(f"{dst} already exists.")
            continue
        print(f"Linking {src} to {dst}.")
        link(src, dst)


def main(args=None):
    arg = p.parse_intermixed_args(args)
    hardlink_files(arg.input, arg.output, arg.all)


if __name__ == '__main__':
    main()
