from ctypes import (
    CDLL,
    c_void_p,
    POINTER,
    byref,
    Structure,
    c_char_p,
    c_float,
    c_short,
    c_size_t
)


class DetectObj(Structure):
    _fields_ = [("encoding", c_char_p), ("confidence", c_float),
                ("bom", c_short)]


chardetlib = CDLL('libchardet.dll')
chardetlib.detect_init.restype = c_void_p
chardetlib.detect_destroy.argtypes = [POINTER(c_void_p)]
chardetlib.detect_obj_init.restype = POINTER(DetectObj)
chardetlib.detect_obj_free.argtypes = [POINTER(POINTER(DetectObj))]
chardetlib.detect_r.argtypes = [c_char_p, c_size_t,
                                POINTER(POINTER(DetectObj))]
chardetlib.detect_r.restype = c_short


def detect_init() -> int:
    return chardetlib.detect_init()


def detect_destroy(Detect: int):
    chardetlib.detect_destroy(byref(c_void_p(Detect)))


def detect_obj_init() -> POINTER(DetectObj):
    return chardetlib.detect_obj_init()


def detect_obj_free(detectObj: POINTER(DetectObj)):
    chardetlib.detect_obj_free(byref(detectObj))


def detect_r(buf: bytes, detectObj: POINTER(DetectObj)) -> int:
    return chardetlib.detect_r(buf, len(buf), byref(detectObj))


if __name__ == "__main__":
    d = detect_init()
    obj = detect_obj_init()
    b = detect_r("你妈死了，这识别不行。WTF，这就是GBK啊。啊啊啊啊啊，为啥不返回GBK啊".encode('UTF-8'), obj)
    print(f'detect_r returned {b}')
    if b == 0:
        print(obj.contents.encoding)
        print(obj.contents.confidence)
    detect_obj_free(obj)
    detect_destroy(d)
    print('All done.')
