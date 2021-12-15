from time import strftime, localtime, timezone
from typing import List
try:
    from dateutil.parser import parse
    have_dateutil = True
except ImportError:
    print('Warning: python-dateutil not found. -s and -e only accept integer now.')  # noqa: E501
    have_dateutil = False


def timeToStr(t: int) -> str:
    te = strftime('%Y-%m-%dT%H:%M:%S', localtime(t))
    op = '-' if timezone > 0 else '+'
    te = te + op + \
        f'{int(abs(timezone)/3600):02}:{int(abs(timezone)%3600/60):02}'
    return te


def tparse(s: str) -> int:
    try:
        return int(s)
    except Exception:
        if have_dateutil:
            return round(parse(s).timestamp())
        else:
            raise ValueError()


def commandLineToArgv(c: str) -> List[str]:
    s = c.split(' ')
    r = []
    t = ''
    f = False
    for i in s:
        if not f and len(i) == 0:
            continue
        if i.startswith('"'):
            if i.endswith('"') and not i.endswith('\\"'):
                r.append(i[1:-1].replace('\\"', '"'))
            else:
                t += i
                f = True
        elif f and i.endswith('"') and not i.endswith('\\"'):
            t += " " + i
            f = False
            r.append(t[1:-1].replace('\\"', '"'))
            t = ''
        elif f:
            t += " " + i
        else:
            r.append(i)
    return r
