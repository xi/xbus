import contextlib
import random

from .schema import parse_schema


class Signal:
    def __init__(self, queue, name, path, iface, signal):
        self.queue = queue
        self.name = name
        self.path = path
        self.iface = iface
        self.signal = signal

    @property
    def rule(self):
        return ','.join(f"{key}='{value}'" for key, value in {
            'type': 'signal',
            'sender': self.name,
            'path': self.path,
            'interface': self.iface,
            'member': self.signal,
        }.items())

    async def __aiter__(self):
        while True:
            msg = await self.queue.get()
            self.queue.task_done()
            # FIXME: msg does not contain well-known sender name
            if (
                msg.path == self.path
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
    async def signal(self, signal):
        async with self.client.signal(*self.defaults, signal) as queue:
            yield queue

    async def get_property(self, prop):
        return await self.client.get_property(*self.defaults, prop)

    async def set_property(self, prop, value):
        return await self.client.set_property(*self.defaults, prop, value)

    async def watch_property(self, prop):
        async for value in self.client.watch_property(*self.defaults, prop):
            yield value

    async def portal_call(self, method, params=()):
        return await self.client.portal_call(*self.defaults, method, params)


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
            (xml,) = await self.con.call(name, path, iface, 'Introspect', ('', []))
            self.introspect_cache[key] = parse_schema(xml)
        return self.introspect_cache[key]

    async def iter_paths(self, name, path=''):
        schema = await self.introspect(name, path or '/')
        if schema.interfaces:
            yield path or '/'
        for child in schema.nodes:
            async for p in self.iter_paths(name, f'{path}/{child}'):
                yield p

    async def guess_iface(self, name, key, value, path, iface=None):
        if iface:
            return iface
        schema = await self.introspect(name, path)
        for iface, s in schema.interfaces.items():
            if value in getattr(s, key):
                return iface
        raise ValueError((name, key, value, path))

    async def guess_path(self, name, key, value, path=None, iface=None):
        if path:
            return path, await self.guess_iface(name, key, value, path, iface)
        async for path in self.iter_paths(name):
            try:
                return path, await self.guess_iface(name, key, value, path, iface)
            except ValueError:
                pass
        raise ValueError((name, key, value))

    async def call(self, name, path, iface, method, params=(), sig=None):
        path, iface = await self.guess_path(name, 'methods', method, path, iface)

        schema = await self.introspect(name, path)
        m = schema.interfaces[iface].methods[method]
        if not sig:
            sig = ''.join(m.args.values())

        result = await self.con.call(name, path, iface, method, (sig, params))

        if len(m.returns) == 1:
            return result[0]
        elif len(m.returns) > 1:
            return result

    @contextlib.asynccontextmanager
    async def signal(self, name, path, iface, signal):
        # NOTE: if we register the same match rule twice and then remove one of
        # them, the other still exists on the bus. So we do not need any
        # special handling on our end.
        path, iface = await self.guess_path(name, 'signals', signal, path, iface)

        with self.con.signal_queue() as queue:
            s = Signal(queue, name, path, iface, signal)
            await self.bus.call('AddMatch', [s.rule], 's')
            try:
                yield s
            finally:
                await self.bus.call('RemoveMatch', [s.rule], 's')

    async def get_property(self, name, path, iface, prop):
        path, iface = await self.guess_path(name, 'properties', prop, path, iface)
        iprop = 'org.freedesktop.DBus.Properties'
        result = await self.con.call(name, path, iprop, 'Get', ('ss', (iface, prop)))
        return result[0]

    async def set_property(self, name, path, iface, prop, value):
        path, iface = await self.guess_path(name, 'properties', prop, path, iface)
        iprop = 'org.freedesktop.DBus.Properties'
        await self.con.call(name, path, iprop, 'Set', ('ssv', (iface, prop, value)))

    async def watch_property(self, name, path, iface, prop):
        path, iface = await self.guess_path(name, 'properties', prop, path, iface)
        iprop = 'org.freedesktop.DBus.Properties'
        async with self.signal(name, path, iprop, 'PropertiesChanged') as queue:
            yield await self.get_property(name, path, iface, prop)
            async for _iface, changed, invalidated in queue:
                if _iface == iface:
                    if prop in changed:
                        yield changed[prop]
                    elif prop in invalidated:
                        yield None

    async def portal_call(self, name, path, iface, method, params=()):
        sender = self.con.unique_name.replace('.', '_')[1:]
        token = str(random.randint(1_000_000_000, 10_000_000_000))
        params[-1]['handle_token'] = ('s', token)
        request_path = f'/org/freedesktop/portal/desktop/request/{sender}/{token}'

        async with self.signal(
            name,
            request_path,
            'org.freedesktop.portal.Request',
            'Response',
        ) as queue:
            await self.call(name, path, iface, method, params)
            async for data in queue:
                return data
