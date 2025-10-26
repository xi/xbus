import asyncio
import os
import socket

from .message import HEADER_ERROR_NAME
from .message import HEADER_REPLY_SERIAL
from .message import MSG_TYPE_ERROR
from .message import MSG_TYPE_METHOD_RETURN
from .message import marshal_method_call
from .message import unmarshal_msg


class DBusError(Exception):
    pass


class Connection:
    def __init__(self, addr='/run/user/1000/bus', loop=None):
        self.addr = addr
        self.loop = loop
        self.serial = 0
        self.replies = {}

        if not self.loop:
            self.loop = asyncio.get_running_loop()

    def get_serial(self):
        self.serial += 1
        return self.serial

    def on_read(self):
        buf = self.sock.recv(134217728)
        if buf:
            header, body = unmarshal_msg(buf)
            if HEADER_REPLY_SERIAL in header.headers:
                serial = header.headers[HEADER_REPLY_SERIAL][1]
                f = self.replies.pop(serial)
                f.set_result((header, body))

    async def send(self, data):
        await self.loop.sock_sendall(self.sock, data)

    async def recv(self, nbytes):
        return await self.loop.sock_recv(self.sock, nbytes)

    async def auth(self):
        uid = os.getuid()
        uid_encoded = str(uid).encode('ascii').hex()
        await self.send(f'AUTH EXTERNAL {uid_encoded}\r\n'.encode('ascii'))
        assert (await self.recv(128)).startswith(b'OK')
        await self.send(b'NEGOTIATE_UNIX_FD\r\n')
        assert (await self.recv(128)).startswith(b'AGREE_UNIX_FD')
        await self.send(b'BEGIN\r\n')

    async def __aenter__(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.setblocking(False)  # noqa
        await self.loop.sock_connect(self.sock, self.addr)

        await self.send(b'\0')
        await self.auth()

        self.loop.add_reader(self.sock.fileno(), self.on_read)

        await self.call(
            'org.freedesktop.DBus',
            '/org/freedesktop/DBus',
            'org.freedesktop.DBus',
            'Hello',
            ('', []),
        )

        return self

    async def __aexit__(self, *args, **kwargs):
        self.sock.shutdown(socket.SHUT_RDWR)

    async def call(self, dest, path, iface, method, params, flags=0):
        serial = self.get_serial()
        f = self.loop.create_future()
        self.replies[serial] = f
        await self.send(marshal_method_call(
            flags, serial, dest, path, iface, method, params)
        )
        header, body = await f
        if header.type == MSG_TYPE_METHOD_RETURN:
            return body
        elif header.type == MSG_TYPE_ERROR:
            raise DBusError(header.headers.get(HEADER_ERROR_NAME))
        else:
            raise ValueError(header.type)


def get_connection(bus):
    if bus == 'session':
        addr = '/run/user/1000/bus'
    else:
        addr = '/run/dbus/system_bus_socket'
    return Connection(addr)
