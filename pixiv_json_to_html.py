from os.path import join, isfile, basename, abspath
from json import load
from html import escape


def pixiv_json_to_html(dir_path):
    json_path = join(dir_path, 'data.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = load(f)
    raw = data['raw']
    title = raw['title']
    html_data = f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>{escape(title)}</title></head><body>\n'
    html_data += f'<h1>{escape(title)}</h1>\n'
    typ = raw['type']
    img_idx = 1
    used = set()
    pbase = basename(abspath(dir_path))
    if typ == 'article':
        blocks = raw['body']['blocks']
        imageMap = raw['body']['imageMap']
        fileMap = raw['body']['fileMap']
        urlEmbedMap = raw['body']['urlEmbedMap']
        for block in blocks:
            block_type = block['type']
            if block_type == 'p':
                text = block['text']
                styles = []
                if 'styles' in block:
                    styles = block['styles']
                events = []
                for style in styles:
                    if style['type'] == 'bold':
                        start = style['offset']
                        end = style['offset'] + style['length']
                        events.append((start, '<b>', False))
                        events.append((end, '</b>', True))
                    else:
                        raise ValueError(f'Unsupported style type: {style["type"]}')
                events.sort(key=lambda x: (x[0], not x[2]))
                output = ""
                last_idx = 0
                for pos, tag, is_closing in events:
                    output += escape(text[last_idx:pos])
                    output += tag
                    last_idx = pos
                output += escape(text[last_idx:])
                html_data += f'<p>{output}</p>\n'
            elif block_type == 'header':
                for key in block:
                    if key not in ['type', 'text']:
                        print(block)
                        raise ValueError(f'Unsupported header block key: {key}')
                text = block['text']
                html_data += f'<h2>{escape(text)}</h2>\n'
            elif block_type == 'image':
                image_id = block['imageId']
                image_url = imageMap[image_id]['originalUrl']
                image_ext = imageMap[image_id]['extension']
                image_path = join(dir_path, f'{pbase}_{img_idx}.{image_ext}')
                if not isfile(image_path):
                    print(image_path)
                    image_path = join(dir_path, f'{image_id}.{image_ext}')
                image_path = basename(image_path)
                html_data += f'<p><img src="{escape(image_path)}" data-original-url="{escape(image_url)}"></p>\n'
                if image_id not in used:
                    used.add(image_id)
                    img_idx += 1
            elif block_type == 'url_embed':
                urlEmbedId = block['urlEmbedId']
                embedData = urlEmbedMap[urlEmbedId]
                embedType = embedData['type']
                if embedType == 'fanbox.post':
                    postInfo = embedData['postInfo']
                    postTitle = postInfo['title']
                    postUrl = f'https://www.fanbox.cc/{postInfo['creatorId']}/posts/{postInfo['id']}'
                    postCover = None
                    if 'cover' in postInfo and postInfo['cover']['type'] == 'cover_image':
                        postCover = postInfo['cover']['url']
                    postExcerpt = postInfo['excerpt']
                    html_data += f'<div class="url-embed"><h2><a href="{escape(postUrl)}">{escape(postTitle)}</a></h2>'
                    if postCover:
                        html_data += f'<p><img src="{escape(postCover)}"></p>'
                    html_data += f'<p>{escape(postExcerpt)}</p></div>\n'
                elif embedType == 'html.card':
                    embed_html_data = embedData['html']
                    html_data += f'<div class="url-embed">{embed_html_data}</div>\n'
                elif embedType == 'html':
                    embed_html_data = embedData['html']
                    html_data += f'<div class="url-embed">{embed_html_data}</div>\n'
                elif embedType == 'default':
                    url = embedData['url']
                    html_data += f'<div class="url-embed"><iframe src="{escape(url)}" /></div>\n'
                else:
                    raise ValueError(f'Unsupported embed type: {embedType}')
            else:
                print(block)
                raise ValueError(f'Unsupported block type: {block_type}')
    elif typ == 'image':
        text = raw['body']['text']
        images = raw['body']['images']
        html_data += f'<p>{escape(text).replace('\n', '<br>')}</p>\n'
        for image in images:
            image_id = image['id']
            image_url = image['originalUrl']
            image_ext = image['extension']
            image_path = join(dir_path, f'{pbase}_{img_idx}.{image_ext}')
            if not isfile(image_path):
                print(image_path)
                image_path = join(dir_path, f'{image_id}.{image_ext}')
            image_path = basename(image_path)
            html_data += f'<p><img src="{escape(image_path)}" data-original-url="{escape(image_url)}"></p>\n'
            img_idx += 1
    else:
        raise ValueError(f'Unsupported body type: {typ}')
    html_data += '</body></html>\n'
    with open(join(dir_path, 'output.html'), 'w', encoding='utf-8') as f:
        f.write(html_data)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Convert Pixiv JSON to HTML')
    parser.add_argument('dir', help='Directory containing data.json')
    args = parser.parse_args()
    pixiv_json_to_html(args.dir)
