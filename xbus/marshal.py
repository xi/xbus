import struct
import types

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


def is_container(type, t):
    return (
        isinstance(type, types.GenericAlias)
        and type.__origin__ is t
    )


def parse_many(i, close=None):
    values = []
    while True:
        v = parse_single(i)
        if v == close:
            return values
        else:
            values.append(v)


def parse_single(i):
    c = next(i)
    try:
        if c == '(':
            return tuple[*parse_many(i, ')')]
        elif c == '{':
            # TODO: validate
            return dict[*parse_many(i, '}')]
        elif c == 'a':
            return list[parse_single(i)]
        else:
            return c
    except StopIteration as e:
        raise ValueError from e


def parse(s):
    i = iter(s)
    values = []
    try:
        while True:
            values.append(parse_single(i))
    except StopIteration:
        return values
    except ValueError as e:
        raise ValueError(s) from e


def get_align(type):
    if type in TYPES:
        return struct.calcsize(TYPES[type])
    elif type in ['g', 'v']:
        return 1
    elif type in ['s', 'o', 'h']:
        return 4
    elif is_container(type, list):
        return 4
    elif is_container(type, tuple) or is_container(type, dict):
        return 8
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
        b, = struct.unpack_from(f'{size}s', buffer=self.buf, offset=self.offset)
        self.offset += size + 1
        return b.decode('utf-8')

    def _read_container(self, type):
        if is_container(type, tuple) or is_container(type, dict):
            return [self.read(t) for t in type.__args__]
        elif is_container(type, list):
            size = self.read('u')
            self.skip_padding(type.__args__[0])
            end = self.offset + size
            arr = []
            while self.offset < end:
                arr.append(self.read(type.__args__[0]))
            if is_container(type.__args__[0], dict):
                return dict(arr)
            return arr
        else:
            raise ValueError(type)

    def read(self, type):
        self.skip_padding(type)
        if type in TYPES:
            format = f'{self.endian}{TYPES[type]}'
            value, = struct.unpack_from(format, buffer=self.buf, offset=self.offset)
            self.offset += struct.calcsize(format)
            return value
        elif type in ['s', 'o', 'g']:
            return self._read_str(type)
        elif type == 'h':  # file descriptor
            i = self.read('u')
            return self.fds[i]
        elif type == 'v':
            sig = self.read('g')
            t = parse(sig)[0]
            v = self.read(t)
            return (sig, v)
        elif isinstance(type, types.GenericAlias):
            return self._read_container(type)
        else:
            raise ValueError(type)

    def unmarshal(self, sig):
        sig = parse(sig)
        return [self.read(t) for t in sig]


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
        self.buf += struct.pack(f'{len(b) + 1}s', b)

    def _write_container(self, type, value):
        if is_container(type, tuple) or is_container(type, dict):
            for t, v in zip(type.__args__, value, strict=True):
                self.write(t, v)
        elif is_container(type, list):
            if is_container(type.__args__[0], dict):
                value = value.items()
            m = Writer(self.endian)
            for v in value:
                m.write(type.__args__[0], v)
            self.write('u', len(m.buf))
            self.write_padding(type.__args__[0])
            self.buf += m.buf
        else:
            raise ValueError(type)

    def write(self, type, value):
        self.write_padding(type)
        if type in TYPES:
            self.buf += struct.pack(f'{self.endian}{TYPES[type]}', value)
        elif type in ['s', 'o', 'g']:
            self._write_str(type, value)
        elif type == 'h':  # file descriptor
            self.write('u', len(self.fds))
            self.fds.append(value.fileno())
        elif type == 'v':
            sig, v = value
            self.write('g', sig)
            for t, value in zip(parse(sig), [v], strict=True):
                self.write(t, value)
        elif isinstance(type, types.GenericAlias):
            self._write_container(type, value)
        else:
            raise ValueError(type)

    def marshal(self, sig, data):
        sig = parse(sig)
        for t, value in zip(sig, data, strict=True):
            self.write(t, value)
