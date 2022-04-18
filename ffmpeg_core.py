from ctypes import (
    CDLL,
    POINTER,
    c_char_p,
    c_float,
    c_int,
    c_int32,
    c_int64,
    c_size_t,
    c_void_p,
    c_wchar_p,
    pointer,
)
from ctypes.util import find_library
from os.path import exists
from typing import List


if exists('ffmpeg_core.dll'):
    dll = 'ffmpeg_core.dll'
else:
    dll = find_library('ffmpeg_core') or find_library('_ffmpeg_core')
dll = CDLL(dll)
free_music_handle = dll.free_music_handle
free_music_handle.restype = None
free_music_handle.argtypes = [c_void_p]
free_music_info_handle = dll.free_music_info_handle
free_music_info_handle.restype = None
free_music_info_handle.argtypes = [c_void_p]
free_ffmpeg_core_settings = dll.free_ffmpeg_core_settings
free_ffmpeg_core_settings.restype = None
free_ffmpeg_core_settings.argtypes = [c_void_p]
free_device_name_list = dll.free_device_name_list
free_device_name_list.restype = None
free_device_name_list.argtypes = [c_void_p]
ffmpeg_core_free = dll.ffmpeg_core_free
ffmpeg_core_free.restype = None
ffmpeg_core_free.argtypes = [c_void_p]
ffmpeg_core_malloc = dll.ffmpeg_core_malloc
ffmpeg_core_malloc.restype = c_void_p
ffmpeg_core_malloc.argtypes = [c_size_t]
ffmpeg_core_realloc = dll.ffmpeg_core_realloc
ffmpeg_core_realloc.restype = c_void_p
ffmpeg_core_realloc.argtypes = [c_void_p, c_size_t]
ffmpeg_core_log_format_line = dll.ffmpeg_core_log_format_line
ffmpeg_core_log_format_line.restype = c_int
ffmpeg_core_log_set_callback = dll.ffmpeg_core_log_set_callback
ffmpeg_core_log_set_callback.restype = None
ffmpeg_core_log_set_flags = dll.ffmpeg_core_log_set_flags
ffmpeg_core_log_set_flags.restype = None
ffmpeg_core_log_set_flags.argtypes = [c_int]
ffmpeg_core_version_str = dll.ffmpeg_core_version_str
ffmpeg_core_version_str.restype = c_char_p
ffmpeg_core_version_str.argtypes = []
ffmpeg_core_version = dll.ffmpeg_core_version
ffmpeg_core_version.restype = c_int32
ffmpeg_core_version.argtypes = []
ffmpeg_core_dump_library_version = dll.ffmpeg_core_dump_library_version
ffmpeg_core_dump_library_version.restype = None
ffmpeg_core_dump_library_version.argtypes = [c_int, c_int]
ffmpeg_core_dump_ffmpeg_configuration = dll.ffmpeg_core_dump_ffmpeg_configuration  # noqa: E501
ffmpeg_core_dump_ffmpeg_configuration.restype = None
ffmpeg_core_dump_ffmpeg_configuration.argtypes = [c_int, c_int]
ffmpeg_core_open = dll.ffmpeg_core_open
ffmpeg_core_open.restype = c_int
ffmpeg_core_open.argtypes = [c_wchar_p, POINTER(c_void_p)]
ffmpeg_core_open2 = dll.ffmpeg_core_open2
ffmpeg_core_open2.restype = c_int
ffmpeg_core_open2.argtypes = [c_wchar_p, POINTER(c_void_p), c_void_p]
ffmpeg_core_open3 = dll.ffmpeg_core_open3
ffmpeg_core_open3.restype = c_int
ffmpeg_core_open3.argtypes = [c_wchar_p, POINTER(c_void_p), c_void_p, c_wchar_p]  # noqa: E501
ffmpeg_core_info_open = dll.ffmpeg_core_info_open
ffmpeg_core_info_open.restype = c_int
ffmpeg_core_info_open.argtypes = [c_wchar_p, POINTER(c_void_p)]
ffmpeg_core_play = dll.ffmpeg_core_play
ffmpeg_core_play.restype = c_int
ffmpeg_core_play.argtypes = [c_void_p]
ffmpeg_core_pause = dll.ffmpeg_core_pause
ffmpeg_core_pause.restype = c_int
ffmpeg_core_pause.argtypes = [c_void_p]
ffmpeg_core_seek = dll.ffmpeg_core_seek
ffmpeg_core_seek.restype = c_int
ffmpeg_core_seek.argtypes = [c_void_p, c_int64]
ffmpeg_core_set_volume = dll.ffmpeg_core_set_volume
ffmpeg_core_set_volume.restype = c_int
ffmpeg_core_set_volume.argtypes = [c_void_p, c_int]
ffmpeg_core_set_speed = dll.ffmpeg_core_set_speed
ffmpeg_core_set_speed.restype = c_int
ffmpeg_core_set_speed.argtypes = [c_void_p, c_float]
ffmpeg_core_set_equalizer_channel = dll.ffmpeg_core_set_equalizer_channel
ffmpeg_core_set_equalizer_channel.restype = c_int
ffmpeg_core_set_equalizer_channel.argtypes = [c_void_p, c_int, c_int]
ffmpeg_core_get_error = dll.ffmpeg_core_get_error
ffmpeg_core_get_error.restype = c_int
ffmpeg_core_get_error.argtypes = [c_void_p]
ffmpeg_core_get_err_msg = dll.ffmpeg_core_get_err_msg
ffmpeg_core_get_err_msg.restype = c_void_p
ffmpeg_core_get_err_msg.argtypes = [c_int]
ffmpeg_core_get_err_msg2 = dll.ffmpeg_core_get_err_msg2
ffmpeg_core_get_err_msg2.restype = c_wchar_p
ffmpeg_core_get_err_msg2.argtypes = [c_int]
ffmpeg_core_get_cur_position = dll.ffmpeg_core_get_cur_position
ffmpeg_core_get_cur_position.restype = c_int64
ffmpeg_core_get_cur_position.argtypes = [c_void_p]
ffmpeg_core_song_is_over = dll.ffmpeg_core_song_is_over
ffmpeg_core_song_is_over.restype = c_int
ffmpeg_core_song_is_over.argtypes = [c_void_p]
ffmpeg_core_get_song_length = dll.ffmpeg_core_get_song_length
ffmpeg_core_get_song_length.restype = c_int64
ffmpeg_core_get_song_length.argtypes = [c_void_p]
ffmpeg_core_info_get_song_length = dll.ffmpeg_core_info_get_song_length
ffmpeg_core_info_get_song_length.restype = c_int64
ffmpeg_core_info_get_song_length.argtypes = [c_void_p]
ffmpeg_core_get_channels = dll.ffmpeg_core_get_channels
ffmpeg_core_get_channels.restype = c_int
ffmpeg_core_get_channels.argtypes = [c_void_p]
ffmpeg_core_info_get_channels = dll.ffmpeg_core_info_get_channels
ffmpeg_core_info_get_channels.restype = c_int
ffmpeg_core_info_get_channels.argtypes = [c_void_p]
ffmpeg_core_get_freq = dll.ffmpeg_core_get_freq
ffmpeg_core_get_freq.restype = c_int
ffmpeg_core_get_freq.argtypes = [c_void_p]
ffmpeg_core_info_get_freq = dll.ffmpeg_core_info_get_freq
ffmpeg_core_info_get_freq.restype = c_int
ffmpeg_core_info_get_freq.argtypes = [c_void_p]
ffmpeg_core_is_playing = dll.ffmpeg_core_is_playing
ffmpeg_core_is_playing.restype = c_int
ffmpeg_core_is_playing.argtypes = [c_void_p]
ffmpeg_core_get_bits = dll.ffmpeg_core_get_bits
ffmpeg_core_get_bits.restype = c_int
ffmpeg_core_get_bits.argtypes = [c_void_p]
ffmpeg_core_info_get_bits = dll.ffmpeg_core_info_get_bits
ffmpeg_core_info_get_bits.restype = c_int
ffmpeg_core_info_get_bits.argtypes = [c_void_p]
ffmpeg_core_get_bitrate = dll.ffmpeg_core_get_bitrate
ffmpeg_core_get_bitrate.restype = c_int
ffmpeg_core_get_bitrate.argtypes = [c_void_p]
ffmpeg_core_info_get_bitrate = dll.ffmpeg_core_info_get_bitrate
ffmpeg_core_info_get_bitrate.restype = c_int
ffmpeg_core_info_get_bitrate.argtypes = [c_void_p]
ffmpeg_core_get_metadata = dll.ffmpeg_core_get_metadata
ffmpeg_core_get_metadata.restype = c_void_p
ffmpeg_core_get_metadata.argtypes = [c_void_p, c_char_p]
ffmpeg_core_info_get_metadata = dll.ffmpeg_core_info_get_metadata
ffmpeg_core_info_get_metadata.restype = c_void_p
ffmpeg_core_info_get_metadata.argtypes = [c_void_p, c_char_p]
ffmpeg_core_init_settings = dll.ffmpeg_core_init_settings
ffmpeg_core_init_settings.restype = c_void_p
ffmpeg_core_init_settings.argtypes = []
version: int = ffmpeg_core_version()
version: List[int] = [i for i in version.to_bytes(4, 'big')]
if version >= [1, 0, 0, 1]:
    ffmpeg_core_is_wasapi_supported = dll.ffmpeg_core_is_wasapi_supported
    ffmpeg_core_is_wasapi_supported.restype = c_int
    ffmpeg_core_is_wasapi_supported.argtypes = []
    ffmpeg_core_settings_set_use_WASAPI = dll.ffmpeg_core_settings_set_use_WASAPI  # noqa: E501
    ffmpeg_core_settings_set_use_WASAPI.restype = c_int
    ffmpeg_core_settings_set_use_WASAPI.argtypes = [c_void_p, c_int]
    ffmpeg_core_settings_set_enable_exclusive = dll.ffmpeg_core_settings_set_enable_exclusive  # noqa: E501
    ffmpeg_core_settings_set_enable_exclusive.restype = c_int
    ffmpeg_core_settings_set_enable_exclusive.argtypes = [c_void_p, c_int]
    ffmpeg_core_settings_set_max_wait_time = dll.ffmpeg_core_settings_set_max_wait_time  # noqa: E501
    ffmpeg_core_settings_set_max_wait_time.restype = c_int
    ffmpeg_core_settings_set_max_wait_time.argtypes = [c_void_p, c_int]
if version >= [1, 0, 0, 2]:
    ffmpeg_core_settings_set_wasapi_min_buffer_time = dll.ffmpeg_core_settings_set_wasapi_min_buffer_time  # noqa: E501
    ffmpeg_core_settings_set_wasapi_min_buffer_time.restype = c_int
    ffmpeg_core_settings_set_wasapi_min_buffer_time.argtypes = [c_void_p, c_int]  # noqa: E501
    ffmpeg_core_set_reverb = dll.ffmpeg_core_set_reverb
    ffmpeg_core_set_reverb.restype = c_int
    ffmpeg_core_set_reverb.argtypes = [c_void_p, c_int, c_float, c_float]


class FFMPEGCoreError(Exception):
    def __init__(self, err: int) -> None:
        self.err = err
        t = ffmpeg_core_get_err_msg(err)
        if t is None:
            if err < 0:
                self.msg = "OOM When getting error message"
            else:
                self.msg = ffmpeg_core_get_err_msg2(err)
        else:
            self.msg = c_wchar_p(t).value
            ffmpeg_core_free(t)
        Exception.__init__(self, f"{self.err} {self.msg}")


class FFMPEGHigherVersionNeededError(Exception):
    pass


class FFMPEGCoreSettings:
    def __init__(self):
        self._h = ffmpeg_core_init_settings()

    def __del__(self):
        if self._h:
            free_ffmpeg_core_settings(self._h)
            self._h = None

    def set_use_WASAPI(self, enable: bool):
        if version >= [1, 0, 0, 1] and ffmpeg_core_is_wasapi_supported():
            return not ffmpeg_core_settings_set_use_WASAPI(self._h, 1 if enable else 0)  # noqa: E501
        else:
            raise Exception('WASAPI is not supported')

    def set_enable_exclusive(self, enable: bool):
        if version >= [1, 0, 0, 1] and ffmpeg_core_is_wasapi_supported():
            return not ffmpeg_core_settings_set_enable_exclusive(self._h, 1 if enable else 0)  # noqa: E501
        else:
            raise Exception('WASAPI is not supported')

    def set_max_wait_time(self, time: int):
        if version >= [1, 0, 0, 1]:
            ffmpeg_core_settings_set_max_wait_time(self._h, time)
        else:
            raise FFMPEGHigherVersionNeededError

    def set_wasapi_min_buffer_time(self, time: int):
        if version >= [1, 0, 0, 2] or ffmpeg_core_is_wasapi_supported():
            return not ffmpeg_core_settings_set_wasapi_min_buffer_time(self._h, time)  # noqa: E501
        else:
            raise Exception('WASAPI is not supported')


class FFMPEGCore:
    def __init__(self, fn: str, settings: FFMPEGCoreSettings = None):
        self._fn = fn
        self._h = c_void_p()
        self._opened = False
        if settings is None:
            r = ffmpeg_core_open(fn, pointer(self._h))
        else:
            r = ffmpeg_core_open2(fn, pointer(self._h), settings._h)
        if r == 0:
            self._opened = True
        else:
            raise FFMPEGCoreError(r)
        self._volume = 100
        self._speed = 1.0

    @property
    def album(self):
        return self['album']

    @property
    def artist(self):
        return self['artist']

    @property
    def bits(self) -> int:
        if self._opened:
            return ffmpeg_core_get_bits(self._h)

    @property
    def bitrate(self) -> int:
        if self._opened:
            return ffmpeg_core_get_bitrate(self._h)

    @property
    def channels(self) -> int:
        if self._opened:
            return ffmpeg_core_get_channels(self._h)

    def clear_reverb(self):
        self.set_reverb(0, 0.0, 0.0)

    def close(self):
        if self._opened:
            free_music_handle(self._h)
            self._opened = False
            self._h = None

    @property
    def freq(self) -> int:
        if self._opened:
            return ffmpeg_core_get_freq(self._h)

    @property
    def is_over(self) -> bool:
        if self._opened:
            return True if ffmpeg_core_song_is_over(self._h) else False

    @property
    def length(self) -> float:
        if self._opened:
            return ffmpeg_core_get_song_length(self._h) / 1E6

    def pause(self):
        if self._opened:
            ffmpeg_core_pause(self._h)

    def play(self):
        if self._opened:
            ffmpeg_core_play(self._h)

    @property
    def playing(self):
        if self._opened:
            return True if ffmpeg_core_is_playing(self._h) else False

    @property
    def position(self) -> float:
        if self._opened:
            return ffmpeg_core_get_cur_position(self._h) / 1E6

    @position.setter
    def position(self, value: float):
        return self.seek(value)

    def seek(self, pos: float):
        pos = int(pos * 1E6)
        if self._opened:
            r = ffmpeg_core_seek(self._h, pos)
            if r:
                raise FFMPEGCoreError(r)

    def set_reverb(self, type: int, mix: float, time: float):
        if self._opened:
            r = ffmpeg_core_set_reverb(self._h, type, mix, time)
            if r:
                raise FFMPEGCoreError(r)

    @property
    def speed(self) -> float:
        return self._speed

    @speed.setter
    def speed(self, v):
        if not isinstance(v, (int, float)):
            raise TypeError("speed must be int or float")
        v = float(v)
        r = ffmpeg_core_set_speed(self._h, v)
        if r == 0:
            self._speed = v
        else:
            raise FFMPEGCoreError(r)

    @property
    def title(self):
        return self['title']

    @property
    def volume(self) -> int:
        return self._volume

    @volume.setter
    def volume(self, v):
        if not isinstance(v, int):
            raise TypeError("volume must be an integer")
        r = ffmpeg_core_set_volume(self._h, v)
        if not r:
            self._volume = v
        else:
            raise FFMPEGCoreError(r)

    def __del__(self):
        if self._opened:
            free_music_handle(self._h)
            self._h = None

    def __getitem__(self, k):
        if not isinstance(k, (str, bytes)):
            raise TypeError("key must be str or bytes")
        if isinstance(k, str):
            k = k.encode()
        if self._opened:
            h = ffmpeg_core_get_metadata(self._h, k)
            if h:
                t = c_wchar_p(h).value
                ffmpeg_core_free(h)
                return t
