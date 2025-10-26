import contextlib

from .schema import parse_schema


def guess_iface(schema, key, value):
    for iface, s in schema.interfaces.items():
        if value in getattr(s, key):
            return iface
    raise ValueError(value)


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


class Client:
    def __init__(self, con):
        self.con = con
        self.introspect_cache = {}

    async def introspect(self, name, path):
        key = f'{name}{path}'
        if key not in self.introspect_cache:
            iface = 'org.freedesktop.DBus.Introspectable'
            xml, = await self.con.call(name, path, iface, 'Introspect', ('', []))
            self.introspect_cache[key] = parse_schema(xml)
        return self.introspect_cache[key]

    async def iter_paths(self, name, path=''):
        schema = await self.introspect(name, path or '/')
        if schema.interfaces:
            yield path or '/'
        for child in schema.nodes:
            async for p in self.iter_paths(name, f'{path}/{child}'):
                yield p

    async def guess_path(self, name):
        async for path in self.iter_paths(name):
            return path
        raise ValueError(name)

    async def call(self, name, method, params=(), path=None, iface=None, sig=None):
        if not path:
            path = await self.guess_path(name)

        schema = await self.introspect(name, path)
        if not iface:
            iface = guess_iface(schema, 'methods', method)

        m = schema.interfaces[iface].methods[method]
        if not sig:
            sig = ''.join(m.args.values())

        result = await self.con.call(name, path, iface, method, (sig, params))

        if len(m.returns) == 1:
            return result[0]
        elif len(m.returns) > 1:
            return result

    async def get_property(self, name, prop, path=None, iface=None):
        if not path:
            path = await self.guess_path(name)

        schema = await self.introspect(name, path)
        if not iface:
            iface = guess_iface(schema, 'properties', prop)

        iprop = 'org.freedesktop.DBus.Properties'
        result = await self.con.call(name, path, iprop, 'Get', ('ss', (iface, prop)))
        return result[0]

    @contextlib.asynccontextmanager
    async def signal(self, name, signal, path=None, iface=None):
        if not path:
            path = await self.guess_path(name)

        schema = await self.introspect(name, path)
        if not iface:
            iface = guess_iface(schema, 'signals', signal)

        with self.con.signal_queue() as queue:
            s = Signal(queue, name, path, iface, signal)

            await self.con.call(
                'org.freedesktop.DBus',
                '/org/freedesktop/DBus',
                'org.freedesktop.DBus',
                'AddMatch',
                ('s', [s.rule]),
            )

            try:
                yield s
            finally:
                await self.con.call(
                    'org.freedesktop.DBus',
                    '/org/freedesktop/DBus',
                    'org.freedesktop.DBus',
                    'RemoveMatch',
                    ('s', [s.rule]),
                )
