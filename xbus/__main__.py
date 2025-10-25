import asyncio

from .glib import BUS_SESSION
from .glib import dbus_call
from .schema import parse_schema
from .utils import async_cache


@async_cache()
async def introspect(bus, name, path):
    iface = 'org.freedesktop.DBus.Introspectable'
    xml, = await dbus_call(bus, name, path, iface, 'Introspect', ('()', []))
    return parse_schema(xml)


async def iter_paths(bus, name, path=''):
    schema = await introspect(bus, name, path or '/')
    if schema['interfaces']:
        yield path or '/'
    for child in schema['nodes']:
        async for p in iter_paths(bus, name, f'{path}/{child}'):
            yield p


async def guess_path(bus, name):
    async for path in iter_paths(bus, name):
        return path
    raise ValueError(name)


def guess_iface(schema, key, value):
    for iface, s in schema['interfaces'].items():
        if value in s[key]:
            return iface
    raise ValueError(value)


async def call(bus, name, method, params=(), path=None, iface=None, sig=None):
    if not path:
        path = await guess_path(bus, name)

    schema = await introspect(bus, name, path)
    if not iface:
        iface = guess_iface(schema, 'methods', method)

    m = schema['interfaces'][iface]['methods'][method]
    if not sig:
        sig = '({})'.format(''.join(m['in'].values()))

    result = await dbus_call(bus, name, path, iface, method, (sig, params))

    if len(m['out']) == 1:
        return result[0]
    elif len(m['out']) > 1:
        return result


async def get_property(bus, name, prop, path=None, iface=None):
    if not path:
        path = await guess_path(bus, name)

    schema = await introspect(bus, name, path)
    if not iface:
        iface = guess_iface(schema, 'properties', prop)

    iprop = 'org.freedesktop.DBus.Properties'
    return await dbus_call(bus, name, path, iprop, 'Get', ('(ss)', (iface, prop)))

# signals -> brauchen dauerhaften glib mainloop


async def amain():
    print(await call(
        BUS_SESSION,
        'org.freedesktop.portal.Desktop',
        'ReadOne',
        ('org.freedesktop.appearance', 'color-scheme'),
    ))
    print(await call(
        BUS_SESSION,
        'org.freedesktop.DBus',
        'ListNames',
    ))
    async for path in iter_paths(BUS_SESSION, 'org.freedesktop.secrets'):
        print(path)
    print(await get_property(
        BUS_SESSION,
        'org.freedesktop.secrets',
        'Collections',
        path='/org/freedesktop/secrets'
    ))


if __name__ == '__main__':
    asyncio.run(amain())
