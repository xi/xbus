import contextlib

from .schema import Schema


class SignalQueue:
    def __init__(self, queue, sender, path, iface, signal):
        self.queue = queue
        self.sender = sender
        self.path = path
        self.iface = iface
        self.signal = signal

    @property
    def rule(self):
        return ','.join(
            f"{key}='{value}'"
            for key, value in {
                'type': 'signal',
                'sender': self.sender,
                'path': self.path,
                'interface': self.iface,
                'member': self.signal,
            }.items()
        )

    async def __aiter__(self):
        async for msg in self.queue:
            if (
                msg.sender == self.sender
                and msg.path == self.path
                and msg.iface == self.iface
                and msg.member == self.signal
            ):
                yield msg.body


class Proxy:
    def __init__(self, client, name, path=None, iface=None):
        self.client = client
        self.defaults = (name, path, iface)

    async def call(self, method, params=(), sig=None):
        return await self.client.call(*self.defaults, method, params, sig)

    @contextlib.asynccontextmanager
    async def subscribe_signal(self, signal):
        async with self.client.subscribe_signal(*self.defaults, signal) as queue:
            yield queue


class Client:
    def __init__(self, con):
        self.con = con
        self.introspect_cache = {}
        self.bus = Proxy(
            self,
            'org.freedesktop.DBus',
            '/org/freedesktop/DBus',
            'org.freedesktop.DBus',
        )

    async def introspect(self, name, path):
        key = f'{name}{path}'
        if key not in self.introspect_cache:
            iface = 'org.freedesktop.DBus.Introspectable'
            (xml,) = await self.con.call(name, path, iface, 'Introspect', [], '')
            self.introspect_cache[key] = Schema.from_xml(xml)
        return self.introspect_cache[key]

    async def call(self, name, path, iface, method, params=(), sig=None):
        schema = await self.introspect(name, path)
        m = schema.interfaces[iface].methods[method]
        if sig is None:
            sig = ''.join([v for _, v in m.args])

        result = await self.con.call(name, path, iface, method, params, sig)
        if len(m.returns) == 1:
            return result[0]
        elif len(m.returns) > 1:
            return result

    @contextlib.asynccontextmanager
    async def subscribe_signal(self, name, path, iface, signal):
        # NOTE: if we register the same match rule twice and then remove one of
        # them, the other still exists on the bus. So we do not need any
        # special handling on our end.

        if not name.startswith(':'):
            name = await self.bus.call('GetNameOwner', [name], 's')
        with self.con.signal_queue() as queue:
            sq = SignalQueue(queue, name, path, iface, signal)
            await self.bus.call('AddMatch', [sq.rule], 's')
            try:
                yield sq
            finally:
                await self.bus.call('RemoveMatch', [sq.rule], 's')
