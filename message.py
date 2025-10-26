from collections import namedtuple

from xbus.marshal import Reader
from xbus.marshal import Writer

MSG_TYPE_METHOD_CALL = 1
MSG_TYPE_METHOD_RETURN = 2
MSG_TYPE_ERROR = 3
MSG_TYPE_SIGNAL = 4

FLAG_NO_REPLY_EXPECTED = 0x1
FLAG_NO_AUTO_START = 0x2
FLAG_ALLOW_INTERACTIVE_AUTHORIZATION = 0x4

VERSION = 1

HEADER_PATH = 1
HEADER_INTERFACE = 2
HEADER_MEMBER = 3
HEADER_ERROR_NAME = 4
HEADER_REPLY_SERIAL = 5
HEADER_DESTINATION = 6
HEADER_SENDER = 7
HEADER_SIGNATURE = 8
HEADER_UNIX_FDS = 9

ENDIAN = {
    '<': 108,
    '>': 66,
}
ENDIAN_REV = {
    108: '<',
    66: '>',
}

MsgHeader = namedtuple('MsgHeader', [
    'endian',
    'type',
    'flags',
    'version',
    'size',
    'serial',
    'headers',
])


def unmarshal_msg(buf):
    r = Reader(buf, ENDIAN_REV[buf[0]])
    header = MsgHeader(*r.unmarshal('yyyyuua{yv}'))
    r.skip_padding(8)
    sig = header.headers.get(HEADER_SIGNATURE, ('g', ''))[1]
    body = r.unmarshal(sig)
    return header, body


def marshal_msg(type, flags, serial, headers, body):
    w_body = Writer('<')
    sig = headers.get(HEADER_SIGNATURE, ('g', ''))[1]
    w_body.marshal(sig, body)

    w = Writer(w_body.endian)
    w.marshal('yyyyuua{yv}', [
        ENDIAN[w.endian],
        type,
        flags,
        VERSION,
        len(w_body.buf),
        serial,
        headers,
    ])
    w.write_padding(8)

    return w.buf + w_body.buf


def marshal_method_call(flags, serial, dest, path, iface, method, params):
    return marshal_msg(
        MSG_TYPE_METHOD_CALL,
        flags,
        serial,
        {
            HEADER_DESTINATION: ('s', dest),
            HEADER_PATH: ('o', path),
            HEADER_INTERFACE: ('s', iface),
            HEADER_MEMBER: ('s', method),
            HEADER_SIGNATURE: ('g', params[0]),
        },
        params[1],
    )


# print(marshal_method_call(0, 1, 'org.freedesktop.portal', '/', 'org.freedesktop.portal.Settings', 'GetAll', ('', [])))
