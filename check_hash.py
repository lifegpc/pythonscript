from argparse import ArgumentParser
import hashlib
import json
from os.path import abspath, exists, getsize, join, relpath
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


OK = 0
CHECKSUM_FAILED = 1
FILE_NOT_EXISTS = 2


p = ArgumentParser(description='Check checksum of files.')
p.add_argument("-m", "--method", help='The hash method to use. Default: auto. Available choices: auto, md5, sha1, sha224, sha256, sha384, sha512.', choices=['auto', 'md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512'], metavar='METHOD', default="auto")  # noqa: E501
p.add_argument("-f", "--file", help="The path to the checksum file. Default: checksum.txt. Releative path is relative to the input directory.", default="checksum.txt")  # noqa: E501
p.add_argument("-o", "--output", help="The path to the result file. Default: .checksum.json. Releative path is relative to the input directory.", default=".checksum.json")  # noqa: E501
p.add_argument("-F", "--force", help="Force rechecking.", action='store_true')
p.add_argument("input", help='The path to the input file or directory.', nargs='*', default=['.'])  # noqa: E501


def checksum(file: str, method: str, task=None, progress=None):
    h = hashlib.new(method)
    with open(file, 'rb') as f:
        while True:
            data = f.read(40960)
            if not data:
                break
            h.update(data)
            if progress is not None and task is not None:
                progress.update(task, advance=len(data))
    return h.hexdigest()


def print_result(result, start: str):
    ok = True
    count = 0
    for i in result:
        r = result[i]
        if r == OK:
            continue
        ok = False
        p = relpath(i, start)
        if r == CHECKSUM_FAILED:
            msg = 'Failed'
        elif r == FILE_NOT_EXISTS:
            msg = 'Not exists'
        print(f"{p}: {msg}")
        count += 1
    if not ok:
        print(f"Total: {count} files failed.")
    else:
        print("All files are OK.")
    return ok


def main(args=None):
    arg = p.parse_intermixed_args(args)
    for input in arg.input:
        result = {}
        result_file = join(input, arg.output)
        if not arg.force:
            try:
                with open(result_file, encoding='UTF-8') as f:
                    result = json.load(f)['result']
            except Exception:
                pass
        checksum_file = join(input, arg.file)
        with open(checksum_file, encoding='UTF-8') as f:
            lines = [i.split("  ") for i in f.readlines() if i.strip()]
            if len(lines) == 0:
                print('No checksum entries found.')
                continue
        if arg.method == 'auto':
            h = lines[0][0]
            if len(h) == 32:
                method = 'md5'
            elif len(h) == 40:
                method = 'sha1'
            elif len(h) == 56:
                method = 'sha224'
            elif len(h) == 64:
                method = 'sha256'
            elif len(h) == 96:
                method = 'sha384'
            elif len(h) == 128:
                method = 'sha512'
            else:
                raise ValueError('Unknown hash method.')
        else:
            method = arg.method
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
            total_tasks = progress.add_task("Checking checksum...",
                                            total=len(lines))
            progress_table = Table.grid()
            progress_table.add_row(progress)
            progress_table.add_row(job_progress)
            live = Live(progress_table, refresh_per_second=10)
            live.start()
        else:
            task = None
            job_progress = None
        files = []
        for line in lines:
            file = abspath(join(input, "  ".join(line[1:]).strip('\n')))
            sum = line[0]
            files.append(file)
            if file in result and result[file] == 0:
                if have_rich:
                    progress.update(total_tasks, advance=1)
                continue
            if not exists(file):
                result[file] = FILE_NOT_EXISTS
                if have_rich:
                    progress.update(total_tasks, advance=1)
                continue
            rp = relpath(file, abspath(input))
            if have_rich:
                task = job_progress.add_task(f"Checking {rp}...",
                                             total=getsize(file))
            try:
                rsum = checksum(file, method, task, job_progress)
                if rsum == sum:
                    result[file] = OK
                    msg = 'OK'
                else:
                    result[file] = CHECKSUM_FAILED
                    msg = 'FAILED'
                if not have_rich:
                    print(f"{rp}: {msg}")
            except Exception:
                result[file] = CHECKSUM_FAILED
            finally:
                if have_rich:
                    progress.update(total_tasks, advance=1)
                    job_progress.remove_task(task)
        if have_rich:
            live.stop()
        if len(result) != len(files):
            result = {i: result[i] for i in result if i in files}
        ok = print_result(result, abspath(input))
        with open(result_file, encoding='UTF-8', mode='w') as f:
            json.dump({'ok': ok, 'result': result}, f, ensure_ascii=False,
                      indent=2)


if __name__ == '__main__':
    main()
