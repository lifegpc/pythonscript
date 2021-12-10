from ctypes import (
    CDLL,
    c_void_p,
    c_char_p,
    c_int
)


libass = CDLL('ass.dll')
libass.ass_library_init.restype = c_void_p
libass.ass_library_done.argtypes = [c_void_p]
libass.ass_set_fonts_dir.argtypes = [c_void_p, c_char_p]
libass.ass_set_fonts.argtypes = [c_void_p, c_char_p, c_char_p, c_int, c_char_p,
                                 c_int]
libass.ass_renderer_init.restype = c_void_p
libass.ass_renderer_init.argtypes = [c_void_p]
libass.ass_renderer_done.argtypes = [c_void_p]


def ass_library_init() -> int:
    return libass.ass_library_init()


def ass_library_done(priv: int):
    libass.ass_library_done(c_void_p(priv))


def ass_set_fonts_dir(priv: int, fonts_dir: str, encoding: str = 'UTF-8'):
    libass.ass_set_fonts_dir(c_void_p(priv),
                             fonts_dir.encode(encoding) if fonts_dir else None)


def ass_renderer_init(priv: int) -> int:
    return libass.ass_renderer_init(c_void_p(priv))


def ass_renderer_done(priv: int):
    libass.ass_renderer_done(c_void_p(priv))


def ass_set_fonts(priv: int, default_font: str, default_family: str, dfp: int,
                  config: str, update: int, encoding: str = 'UTF-8'):
    libass.ass_set_fonts(c_void_p(priv),
                         default_font.encode(encoding) if default_font else None,  # noqa: E501
                         default_family.encode(encoding) if default_family else None,  # noqa: E501
                         dfp, config.encode(encoding) if config else None,
                         update)


if __name__ == "__main__":
    priv = ass_library_init()
    print(f'Created ASS_LIBARAY Handle: {priv}')
    font_dir = "E:\\fonts-test-来点中文\\"
    ass_set_fonts_dir(priv, font_dir)
    print(f'Set fonts dir to "{font_dir}" (UTF-8)')
    da_font = font_dir + "\\文道奶酪体.ttf"
    fconfig = "D:\\programs\\fonts"
    print('Call ass_renderer_init')
    red = ass_renderer_init(priv)
    print(f'Call ass_set_fonts with {da_font}, NULL, 1, {fconfig}, 1)')
    ass_set_fonts(red, da_font, None, 1, fconfig, 1)
    print('Free ass_renderer')
    ass_renderer_done(red)
    ass_set_fonts_dir(priv, font_dir, 'GB2312')
    print(f'Set fonts dir to "{font_dir}" (GB2312(ANSI))')
    print('Call ass_renderer_init')
    red = ass_renderer_init(priv)
    print(f'Call ass_set_fonts with {da_font}, NULL, 1, {fconfig}, 1)')
    ass_set_fonts(red, da_font, None, 1, fconfig, 1, 'GB2312')
    print('Free ass_renderer')
    ass_renderer_done(red)
    print('Test chars don\'t exist in GB2312.')
    font_dir = 'E:\\微软必须死个🐴'
    ass_set_fonts_dir(priv, font_dir)
    print(f'Set fonts dir to "{font_dir}" (UTF-8)')
    print('Call ass_renderer_init')
    red = ass_renderer_init(priv)
    print(f'Call ass_set_fonts with {da_font}, NULL, 1, {fconfig}, 1)')
    ass_set_fonts(red, da_font, None, 1, fconfig, 1)
    print('Free ass_renderer')
    ass_renderer_done(red)
    ass_library_done(priv)
    print('Free Handle.')
