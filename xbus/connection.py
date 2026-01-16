import asyncio
import os
import socket
from contextlib import contextmanager

from .message import Msg
from .message import MsgFlag
from .message import MsgType


class DBusError(Exception):
    pass


class Connection:
    def __init__(self, addr, loop=None):
        self.addr = addr
        self.loop = loop
        self.serial = 0
        self.queue = []
        self.replies = {}
        self.signal_queues = set()

        if not self.loop:
            self.loop = asyncio.get_running_loop()

    def get_serial(self):
        self.serial += 1
        return self.serial

    def on_read(self):
        buf, fds, _, _ = socket.recv_fds(self.sock, 134217728, 255)
        if buf:
            msg = Msg.unmarshal(buf, fds)
            if msg.reply_serial is not None:
                f = self.replies.pop(msg.reply_serial)
                f.set_result(msg)
            elif msg.type == MsgType.SIGNAL:
                for queue in self.signal_queues:
                    queue.put_nowait(msg)
            else:
                raise ValueError(msg)

    def on_write(self):
        if self.queue:
            buf, fds, f = self.queue.pop(0)
            socket.send_fds(self.sock, [buf], fds)
            f.set_result(None)
        else:
            self.loop.remove_writer(self.sock.fileno())

    async def send(self, buf, fds=[]):
        if not self.queue:
            self.loop.add_writer(self.sock.fileno(), self.on_write)
        f = self.loop.create_future()
        self.queue.append((buf, fds, f))
        await f

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

        self.unique_name, = await self.call(
            'org.freedesktop.DBus',
            '/org/freedesktop/DBus',
            'org.freedesktop.DBus',
            'Hello',
            ('', []),
        )

        return self

    async def __aexit__(self, *args, **kwargs):
        self.sock.shutdown(socket.SHUT_RDWR)

    @contextmanager
    def signal_queue(self):
        queue = asyncio.Queue()
        self.signal_queues.add(queue)
        try:
            yield queue
        finally:
            self.signal_queues.remove(queue)
            queue.shutdown()

    async def call(self, dest, path, iface, method, params, flags=MsgFlag.NONE):
        request = Msg(
            MsgType.METHOD_CALL,
            self.get_serial(),
            destination=dest,
            path=path,
            iface=iface,
            member=method,
            sig=params[0],
            body=params[1],
            flags=flags,
        )

        if flags & MsgFlag.NO_REPLY_EXPECTED:
            await self.send(*request.marshal())
            return

        f = self.loop.create_future()
        self.replies[request.serial] = f

        await self.send(*request.marshal())

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
            'DBUS_SESSION_BUS_ADDRESS',
            f'unix:path=/run/user/{os.getuid()}/bus',
        )
    else:
        addr = os.getenv(
            'DBUS_SYSTEM_BUS_ADDRESS',
            'unix:path=/run/dbus/system_bus_socket',
        )
    return Connection(addr.removeprefix('unix:path='))
