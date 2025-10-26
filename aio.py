import asyncio
import os
import socket

from message import HEADER_REPLY_SERIAL
from message import marshal_method_call
from message import unmarshal_msg


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
        return await f


async def amain():
    async with Connection() as con:
        print(await con.call(
            'org.freedesktop.portal.Desktop',
            '/org/freedesktop/portal',
            'org.freedesktop.portal.Settings',
            'ReadOne',
            ('ss', ('org.freedesktop.appearance', 'color-scheme')),
        ))


asyncio.run(amain())
