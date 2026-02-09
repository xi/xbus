import asyncio

from . import get_client
from .client import Proxy


async def amain():
    async with get_client('session') as c:
        desktop_proxy = Proxy(c, 'org.freedesktop.portal.Desktop')

        print(await desktop_proxy.call(
            'ReadOne',
            ('org.freedesktop.appearance', 'color-scheme'),
        ))
        print(await c.call('org.freedesktop.DBus', None, None, 'ListNames'))
        async for path in c.iter_paths('org.freedesktop.secrets'):
            print(path)
        print(await c.get_property(
            'org.freedesktop.secrets',
            '/org/freedesktop/secrets',
            None,
            'Collections',
        ))

        with open(__file__) as fh:
            print(await desktop_proxy.portal_call(
                'OpenFile',
                ['', fh, {}],
            ))

        async with desktop_proxy.signal('SettingChanged') as queue:
            async for value in queue:
                print(value)


if __name__ == '__main__':
    asyncio.run(amain())
