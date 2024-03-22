from argparse import ArgumentParser
import hashlib
from os import listdir
from os.path import getsize, isdir, isfile, join, relpath
try:
    from rich.live import Live
    from rich.progress import (
        Progress,
        SpinnerColumn,
        BarColumn,
        TextColumn,
        TimeRemainingColumn,
        TransferSpeedColumn,
        DownloadColumn,
        MofNCompleteColumn,
    )
    from rich.table import Table
    have_rich = True
except ImportError:
    have_rich = False


p = ArgumentParser(description='Generate checksum of files.')
p.add_argument("-o", "--output", help='The path to output file. Default: checksum.txt. Releative path is relative to the input directory.', default="checksum.txt")  # noqa: E501
p.add_argument("-m", "--method", help='The hash method to use. Default: md5. Available choices: md5, sha1, sha224, sha256, sha384, sha512.', choices=['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512'], metavar='METHOD', default="md5")  # noqa: E501
p.add_argument("input", help='The path to the input file or directory.', nargs='*', default=['.'])  # noqa: E501


def list_files(input: str, output=None):
    files = []
    for i in listdir(input):
        path = join(input, i)
        if isfile(path):
            files.append(path)
        elif isdir(path):
            files.extend(list_files(path, None))
    if output is not None:
        output_file = join(input, output)
        if output_file in files:
            files.remove(output_file)
    return files


def cal_hash(file: str, method: str, task=None, progress=None):
    h = hashlib.new(method)
    with open(file, 'rb') as f:
        while True:
            data = f.read(40960)
            if not data:
                break
            h.update(data)
            if progress is not None and task is not None:
                progress.update(task, advance=len(data))
    t = f"{h.hexdigest()}  {file}\n"
    if progress is None or task is None:
        print(t)
    return t


def main(args=None):
    arg = p.parse_intermixed_args(args)
    for i in arg.input:
        files = list_files(i, arg.output)
        output_file = join(i, arg.output)
        with open(output_file, encoding='UTF-8', mode='w', newline='\n') as f:
            if have_rich:
                progress = Progress("{task.description}",
                                    SpinnerColumn(),
                                    BarColumn(),
                                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),  # noqa: E501
                                    MofNCompleteColumn(),
                                    )
                job_progress = Progress("{task.description}",
                                        SpinnerColumn(),
                                        BarColumn(),
                                        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),  # noqa: E501
                                        DownloadColumn(),
                                        TransferSpeedColumn(),
                                        TimeRemainingColumn(),
                                        )
                total_tasks = progress.add_task("Generating checksum...",
                                                total=len(files))
                progress_table = Table.grid()
                progress_table.add_row(progress)
                progress_table.add_row(job_progress)
                live = Live(progress_table, refresh_per_second=10)
                try:
                    live.start()
                    for pa in files:
                        rp = relpath(pa, i)
                        task = job_progress.add_task(f"Calculating {rp}...",
                                                     total=getsize(pa))
                        f.write(cal_hash(pa, arg.method, task, job_progress))
                        progress.update(total_tasks, advance=1)
                        job_progress.remove_task(task)
                finally:
                    progress.stop()
                    job_progress.stop()
                    live.stop()
            else:
                for i in files:
                    f.write(cal_hash(i, arg.method))


if __name__ == '__main__':
    main()
