import struct
from dataclasses import dataclass

TYPES = {
    'y': 'b',  # byte
    'b': 'I',  # bool
    'n': 'h',  # int16
    'q': 'H',  # uint16
    'i': 'i',  # int32
    'u': 'I',  # uint32
    'x': 'q',  # int64
    't': 'Q',  # uint64
    'd': 'd',  # float
}

@dataclass
class DictItem:
    key: str
    value: str


@dataclass
class List:
    value: str


def _parse_single(sig_iter):
    c = next(sig_iter)
    try:
        if c == '(':
            values = []
            while True:
                v = _parse_single(sig_iter)
                if v == ')':
                    break
                values.append(v)
            return tuple(values)
        elif c == '{':
            key = _parse_single(sig_iter)
            value = _parse_single(sig_iter)
            if next(sig_iter) != '}':
                raise ValueError
            return DictItem(key, value)
        elif c == 'a':
            return List(_parse_single(sig_iter))
        else:
            return c
    except StopIteration as e:
        raise ValueError from e


def parse(sig):
    sig_iter = iter(sig)
    values = []
    try:
        while True:
            values.append(_parse_single(sig_iter))
    except ValueError as e:
        raise ValueError(sig) from e
    except StopIteration:
        return values


def get_align(type):
    if isinstance(type, List):
        return 4
    elif isinstance(type, (DictItem, tuple)):
        return 8
    elif type in TYPES:
        return struct.calcsize(f'={TYPES[type]}')
    elif type in ['g', 'v']:
        return 1
    elif type in ['s', 'o', 'h']:
        return 4
    raise ValueError(type)


class Reader:
    def __init__(self, buf, fds, endian):
        self.buf = buf
        self.fds = fds
        self.endian = endian
        self.offset = 0

    def skip_padding(self, align):
        if not isinstance(align, int):
            align = get_align(align)
        self.offset += (align - self.offset) % align

    def _read_str(self, type):
        if type == 'g':
            size = self.read('y')
        else:
            size = self.read('u')
        (b,) = struct.unpack_from(f'{size}s', buffer=self.buf, offset=self.offset)
        self.offset += size + 1
        return b.decode('utf-8')

    def _read_list(self, value_type):
        size = self.read('u')
        self.skip_padding(value_type)
        end = self.offset + size
        arr = []
        while self.offset < end:
            arr.append(self.read(value_type))
        if isinstance(value_type, DictItem):
            return dict(arr)
        return arr

    def read(self, type):
        self.skip_padding(type)
        if isinstance(type, List):
            return self._read_list(type.value)
        elif isinstance(type, DictItem):
            return self.read(type.key), self.read(type.value)
        elif isinstance(type, tuple):
            return tuple([self.read(t) for t in type])
        elif type in TYPES:
            format = f'{self.endian}{TYPES[type]}'
            (value,) = struct.unpack_from(format, buffer=self.buf, offset=self.offset)
            self.offset += struct.calcsize(format)
            return value
        elif type in ['s', 'o', 'g']:
            return self._read_str(type)
        elif type == 'h':  # file descriptor
            i = self.read('u')
            return self.fds[i]
        elif type == 'v':
            sig = self.read('g')
            (t,) = parse(sig)
            v = self.read(t)
            return (sig, v)
        else:
            raise ValueError(type)

    def unmarshal(self, sig):
        sig = parse(sig)
        return tuple([self.read(t) for t in sig])


class Writer:
    def __init__(self, endian):
        self.buf = b''
        self.fds = []
        self.endian = endian

    def write_padding(self, align):
        if not isinstance(align, int):
            align = get_align(align)
        self.buf += b'\0' * ((align - len(self.buf)) % align)

    def _write_str(self, type, value):
        b = value.encode('utf-8')
        if type == 'g':
            self.write('y', len(b))
        else:
            self.write('u', len(b))
        self.buf += struct.pack(f'{self.endian}{len(b) + 1}s', b)

    def _write_list(self, value_type, value):
        if isinstance(value_type, DictItem):
            value = value.items()
        subwriter = Writer(self.endian)
        for v in value:
            subwriter.write(value_type, v)
        self.write('u', len(subwriter.buf))
        self.write_padding(value_type)
        self.buf += subwriter.buf

    def write(self, type, value):
        self.write_padding(type)
        if isinstance(type, List):
            self._write_list(type.value, value)
        elif isinstance(type, DictItem):
            k, v = value
            self.write(type.key, k)
            self.write(type.value, v)
        elif isinstance(type, tuple):
            for t, v in zip(type, value, strict=True):
                self.write(t, v)
        elif type in TYPES:
            self.buf += struct.pack(f'{self.endian}{TYPES[type]}', value)
        elif type in ['s', 'o', 'g']:
            self._write_str(type, value)
        elif type == 'h':  # file descriptor
            self.write('u', len(self.fds))
            self.fds.append(value if isinstance(value, int) else value.fileno())
        elif type == 'v':
            sig, v = value
            (t,) = parse(sig)
            self.write('g', sig)
            self.write(t, v)
        else:
            raise ValueError(type)

    def marshal(self, sig, data):
        sig = parse(sig)
        for t, value in zip(sig, data, strict=True):
            self.write(t, value)
