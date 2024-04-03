from argparse import ArgumentParser
import music_tag
import taglib

p = ArgumentParser()
p.add_argument('infile')
p.add_argument('outfile')


def main():
    arg = p.parse_args()
    with taglib.File(arg.infile) as f:
        with taglib.File(arg.outfile) as o:
            o.tags.update(f.tags)
            o.save()
    i = music_tag.load_file(arg.infile)
    o = music_tag.load_file(arg.outfile)
    o["artwork"] = i["artwork"]
    o.save()


if __name__ == '__main__':
    main()
