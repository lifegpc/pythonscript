from argparse import ArgumentParser
from http.cookiejar import MozillaCookieJar
from re import compile
from urllib.parse import urlparse
from bs4 import BeautifulSoup, Tag
from ebooklib.epub import (
    EpubBook,
    EpubHtml,
    EpubItem,
    EpubNav,
    EpubNcx,
    Link,
    write_epub,
)
from requests import Session
from time import sleep


RE = compile(r'https?://(?:www\.)?ireader\.com\.cn\/index.php\?.*?bid\=(\d+)')
URL_RE = compile(r'url\((https?:[^)]+)\)')


class RawEpubHtml(EpubHtml):
    def get_content(self):
        return self.content


class Span:
    def __init__(self, title: str):
        self.title = title


def get_url_name(url):
    return urlparse(url).path.split('/')[-1]


def get_book_id(url):
    try:
        return int(url)
    except Exception:
        pass
    m = RE.match(url)
    if m:
        return int(m.group(1))
    raise ValueError('无法解析书籍ID')


def parse_book_detail(data):
    soup = BeautifulSoup(data, 'html.parser')
    name = list(soup.find('div', class_='bookname').children)
    for n in name:
        if isinstance(n, Tag):
            name = n
            break
    name = name.contents[0].contents[0]
    print(name)
    author = soup.find('span', class_="author").contents[0].strip("作者：")
    print(author)
    desc = list(soup.find('div', class_="bookinf03").children)
    for n in desc:
        if isinstance(n, Tag):
            desc = n
            break
    desc = desc.contents[0].strip()
    print(desc)
    cover = soup.find('div', class_='bookL')
    cover: Tag = cover.find_all('img')[0]
    cover = cover.attrs['src']
    print(cover)
    return {"name": name, "author": author, "desc": desc, "cover": cover}


class DownIreader:
    def __init__(self, cookies: str = None) -> None:
        self._ses = Session()
        self._cookies = cookies
        if self._cookies:
            self._ses.cookies = MozillaCookieJar(self._cookies)
            self._ses.cookies.load()

    def __del__(self):
        if self._cookies and isinstance(self._ses.cookies, MozillaCookieJar):
            self._ses.cookies.save()

    def get(self, url):
        r = self._ses.get(url)
        if r.status_code >= 400:
            raise RuntimeError(f'请求失败: {r.status_code} {r.reason}')
        return r

    def get_book_detail(self, bid: int):
        r = self._ses.get("https://www.ireader.com.cn/index.php?ca=bookdetail.index", params={"bid": str(bid)})  # noqa: E501
        if r.status_code >= 400:
            raise RuntimeError(f'获取书籍详情失败: {r.status_code} {r.reason}')
        return r

    def get_page(self, bid: int, page: int):
        d = {"bid": str(bid), "cid": str(page)}
        r = self._ses.get("https://www.ireader.com.cn/index.php?ca=Chapter.Content", params=d)  # noqa: E501
        if r.status_code >= 400:
            raise RuntimeError(f'获取书籍章节内容失败: {r.status_code} {r.reason}')  # noqa: E501
        return r

    def get_page_list(self, bid: int, page: int = None):
        dp = False
        if page is None:
            page = "1"
            dp = True
        d = {"bid": str(bid), "page": page, "pageSize": "100"}
        r = self._ses.get("https://www.ireader.com.cn/index.php?ca=Chapter.List&ajax=1", params=d)  # noqa: E501
        if r.status_code >= 400:
            raise RuntimeError(f'获取书籍章节列表失败: {r.status_code} {r.reason}')
        data = r.json()
        if not dp:
            return data
        li = []
        li += data["list"]
        tp = data["page"]["totalPage"]
        for i in range(2, tp + 1):
            li += self.get_page_list(bid, i)["list"]
        return li


def main():
    p = ArgumentParser(description='从掌阅下载书籍')
    p.add_argument('URL', help='掌阅书籍链接/ID')
    p.add_argument('-o', '--output', help='输出文件名', dest='output')
    p.add_argument('-c', '--cookies', help='cookies文件', dest='cookies')
    p.add_argument('-t', '--treat-wordcount', help='字数为0时，当作父章节处理。', dest="twc", action="store_true")  # noqa: E501
    arg = p.parse_intermixed_args()
    bid = get_book_id(arg.URL)
    print('书籍ID:', bid)
    dr = DownIreader(arg.cookies)
    detail = dr.get_book_detail(bid)
    bd = parse_book_detail(detail.text)
    output = arg.output or f'{bd["name"]} - {bd["author"]}.epub'
    book = EpubBook()
    resources = []
    cover_url = bd['cover']
    cover_name = get_url_name(cover_url)
    resources.append(cover_name)
    book.set_cover(cover_name, dr.get(cover_url).content)
    book.set_title(bd['name'])
    book.set_identifier(str(bid))
    book.add_metadata('DC', 'identifier', str(bid), {'id': 'zyid'})
    book.set_language('zh-CN')
    book.add_author(bd["author"])
    pages = dr.get_page_list(bid)
    top_tocs = [bd["name"]]
    tocs = top_tocs
    curr_ses = None
    first_page_in_toc = False
    for p in pages:
        if arg.twc and p["wordCount"] == 0:
            first_page_in_toc = True
            if curr_ses == p["chapterName"]:
                continue
            ntocs = []
            top_tocs.append([Span(p["chapterName"]), ntocs])
            tocs = ntocs
            curr_ses = p["chapterName"]
            continue
        elif arg.twc and not first_page_in_toc:
            curr_ses = None
            tocs = top_tocs
        print(f'正在下载第{p["id"]}章')
        res = dr.get_page(bid, p["id"])
        pa = BeautifulSoup(res.text, 'lxml')
        for i in pa.descendants:
            if isinstance(i, Tag):
                if i.name == 'img':
                    if 'src' in i.attrs:
                        src = i.attrs['src']
                        name = get_url_name(src)
                        if name not in resources:
                            resources.append(name)
                            book.add_item(EpubItem(file_name=name, content=dr.get(src).content))  # noqa: E501
                        i.attrs['src'] = name
                elif i.name == 'link':
                    if 'rel' in i.attrs:
                        if 'stylesheet' in i.attrs['rel']:
                            if 'href' in i.attrs:
                                href = i.attrs['href']
                                name = get_url_name(href)
                                if name not in resources:
                                    resources.append(name)
                                    book.add_item(EpubItem(file_name=name, content=dr.get(href).content))  # noqa: E501
                                i.attrs['href'] = name
                if 'style' in i.attrs:
                    s = i.attrs['style']
                    m = URL_RE.search(s)
                    while m is not None:
                        src = m.group(1)
                        name = get_url_name(src)
                        if name not in resources:
                            resources.append(name)
                            book.add_item(EpubItem(file_name=name, content=dr.get(src).content))  # noqa: E501
                        s = s.replace(src, name)
                        m = URL_RE.search(s)
                    i.attrs['style'] = s
        data = pa.encode(formatter="html5")
        c = RawEpubHtml(f'{p["id"]}.html', file_name=f'{p["id"]}.html', content=data, title=p["chapterName"])  # noqa: E501
        book.add_item(c)
        tocs.append(Link(f'{p["id"]}.html', p["chapterName"], f'{p["id"]}.html'))  # noqa: E501
        book.spine.append(c)
        sleep(1)
        if arg.twc:
            first_page_in_toc = False
    for i in tocs:
        if isinstance(i, list):
            i[0] = Link(i[1][0].href, i[0].title, i[1][0].uid)
    book.toc = tocs
    book.add_item(EpubNav())
    book.add_item(EpubNcx())
    write_epub(output, book)


if __name__ == '__main__':
    main()
