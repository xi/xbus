import struct
from dataclasses import dataclass

TYPES = {
    'y': 'B',  # byte
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


def parse_sig(sig):
    sig_iter = iter(sig)
    values = []
    try:
        while True:
            values.append(_parse_single(sig_iter))
    except ValueError as e:
        raise ValueError(sig) from e
    except StopIteration:
        return values


def get_align(typ):
    if isinstance(typ, List):
        return 4
    elif isinstance(typ, (DictItem, tuple)):
        return 8
    elif typ in TYPES:
        return struct.calcsize(f'={TYPES[typ]}')
    elif typ in ['g', 'v']:
        return 1
    elif typ in ['s', 'o', 'h']:
        return 4
    raise ValueError(typ)


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

    def _read_str(self, typ):
        if typ == 'g':
            size = self.read('y')
        else:
            size = self.read('u')
        (b,) = struct.unpack_from(f'{size}s', buffer=self.buf, offset=self.offset)
        self.offset += size + 1
        return b.decode('utf-8')

    def _read_list(self, value_typ):
        size = self.read('u')
        self.skip_padding(value_typ)
        end = self.offset + size
        arr = []
        while self.offset < end:
            arr.append(self.read(value_typ))
        if isinstance(value_typ, DictItem):
            return dict(arr)
        return arr

    def read(self, typ):
        self.skip_padding(typ)
        if isinstance(typ, List):
            return self._read_list(typ.value)
        elif isinstance(typ, DictItem):
            return self.read(typ.key), self.read(typ.value)
        elif isinstance(typ, tuple):
            return tuple([self.read(t) for t in typ])
        elif typ in TYPES:
            format = f'{self.endian}{TYPES[typ]}'
            (value,) = struct.unpack_from(format, buffer=self.buf, offset=self.offset)
            self.offset += struct.calcsize(format)
            return value
        elif typ in ['s', 'o', 'g']:
            return self._read_str(typ)
        elif typ == 'h':  # file descriptor
            i = self.read('u')
            return self.fds[i]
        elif typ == 'v':
            sig = self.read('g')
            (t,) = parse_sig(sig)
            v = self.read(t)
            return (sig, v)
        else:  # pragma: no cover
            raise ValueError(typ)

    def unmarshal(self, sig):
        typ = parse_sig(sig)
        return tuple([self.read(t) for t in typ])


class Writer:
    def __init__(self, endian):
        self.buf = b''
        self.fds = []
        self.endian = endian

    def write_padding(self, align):
        if not isinstance(align, int):
            align = get_align(align)
        self.buf += b'\0' * ((align - len(self.buf)) % align)

    def _write_str(self, typ, value):
        b = value.encode('utf-8')
        if typ == 'g':
            self.write('y', len(b))
        else:
            self.write('u', len(b))
        self.buf += struct.pack(f'{self.endian}{len(b) + 1}s', b)

    def _write_list(self, value_typ, value):
        if isinstance(value_typ, DictItem):
            value = value.items()
        subwriter = Writer(self.endian)
        for v in value:
            subwriter.write(value_typ, v)
        self.write('u', len(subwriter.buf))
        self.write_padding(value_typ)
        self.buf += subwriter.buf

    def write(self, typ, value):
        self.write_padding(typ)
        if isinstance(typ, List):
            self._write_list(typ.value, value)
        elif isinstance(typ, DictItem):
            k, v = value
            self.write(typ.key, k)
            self.write(typ.value, v)
        elif isinstance(typ, tuple):
            for t, v in zip(typ, value, strict=True):
                self.write(t, v)
        elif typ in TYPES:
            self.buf += struct.pack(f'{self.endian}{TYPES[typ]}', value)
        elif typ in ['s', 'o', 'g']:
            self._write_str(typ, value)
        elif typ == 'h':  # file descriptor
            self.write('u', len(self.fds))
            self.fds.append(value if isinstance(value, int) else value.fileno())
        elif typ == 'v':
            sig, v = value
            (t,) = parse_sig(sig)
            self.write('g', sig)
            self.write(t, v)
        else:  # pragma: no cover
            raise ValueError(typ)

    def marshal(self, sig, data):
        typ = parse_sig(sig)
        for t, value in zip(typ, data, strict=True):
            self.write(t, value)
