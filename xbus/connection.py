import asyncio
import os
import socket

from .message import Msg
from .message import MsgType


class DBusError(Exception):
    pass


class Connection:
    def __init__(self, addr, loop=None):
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
            msg = Msg.unmarshal(buf)
            if msg.reply_serial is not None:
                f = self.replies.pop(msg.reply_serial)
                f.set_result(msg)

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

        request = Msg(
            MsgType.METHOD_CALL,
            serial,
            destination=dest,
            path=path,
            iface=iface,
            member=method,
            sig=params[0],
            body=params[1],
            flags=flags,
        )
        await self.send(request.marshal())

        response = await f
        if response.type == MsgType.METHOD_RETURN:
            return response.body
        elif response.type == MsgType.ERROR:
            raise DBusError(response.error_name)
        else:
            raise ValueError(response.type)


def get_connection(bus):
    if bus == 'session':
        addr = os.getenv(
            'DBUS_SESSION_BUS_ADDRESS2',
            f'unix:path=/run/user/{os.getuid()}/bus',
        )
    else:
        addr = os.getenv(
            'DBUS_SESSION_BUS_ADDRESS',
            'unix:path=/run/dbus/system_bus_socket',
        )
    return Connection(addr.removeprefix('unix:path='))
