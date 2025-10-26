import enum
from dataclasses import dataclass

from .marshal import Reader
from .marshal import Writer

VERSION = 1

ENDIAN = {
    '<': 108,
    '>': 66,
}
ENDIAN_REV = {
    108: '<',
    66: '>',
}


class Header(enum.IntEnum):
    path = 1
    iface = 2
    member = 3
    error_name = 4
    reply_serial = 5
    destination = 6
    sender = 7
    sig = 8
    unix_fds = 9

    def get_sig(self):
        return {
            self.path: 'o',
            self.reply_serial: 'u',
            self.sig: 'g',
            self.unix_fds: 'u',
        }.get(self, 's')


class MsgType(enum.IntEnum):
    METHOD_CALL = 1
    METHOD_RETURN = 2
    ERROR = 3
    SIGNAL = 4


class MsgFlag(enum.Flag):
    NONE = 0x0
    NO_REPLY_EXPECTED = 0x1
    NO_AUTO_START = 0x2
    ALLOW_INTERACTIVE_AUTHORIZATION = 0x4


@dataclass
class Msg:
    type: MsgType
    serial: int
    flags: MsgFlag = MsgFlag.NONE
    reply_serial: int = None
    sender: str = None
    destination: str = None
    path: str = None
    iface: str = None
    member: str = None
    error_name: str = None
    unix_fds: str = None
    sig: str = ''
    body: str = ()

    def marshal(self, endian='<'):
        w_body = Writer(endian)
        w_body.marshal(self.sig, self.body)

        headers = {}
        for header in Header:
            value = getattr(self, header.name)
            if value is not None:
                headers[header.value] = header.get_sig(), value

        w = Writer(endian)
        w.marshal('yyyyuua{yv}', [
            ENDIAN[endian],
            self.type,
            self.flags.value,
            VERSION,
            len(w_body.buf),
            self.serial,
            headers,
        ])
        w.write_padding(8)

        return w.buf + w_body.buf

    @classmethod
    def unmarshal(cls, buf):
        r = Reader(buf, ENDIAN_REV[buf[0]])
        r.offset += 1

        type, flags, version, _size, serial, headers = r.unmarshal('yyyuua{yv}')
        if version != VERSION:
            raise ValueError(version)

        msg = cls(MsgType(type), serial, MsgFlag(flags))

        for header in Header:
            if header.value in headers:
                value = headers[header.value]
                if value[0] != header.get_sig():
                    raise ValueError(header, value)
                setattr(msg, header.name, value[1])

        r.skip_padding(8)
        msg.body = r.unmarshal(msg.sig)

        return msg
