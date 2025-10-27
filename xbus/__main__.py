import asyncio

from .client import Client
from .connection import get_connection


async def amain():
    async with get_connection('session') as con:
        c = Client(con)
        print(await c.call(
            'org.freedesktop.portal.Desktop',
            'ReadOne',
            ('org.freedesktop.appearance', 'color-scheme'),
        ))
        print(await c.call(
            'org.freedesktop.DBus',
            'ListNames',
        ))
        async for path in c.iter_paths('org.freedesktop.secrets'):
            print(path)
        print(await c.get_property(
            'org.freedesktop.secrets',
            'Collections',
            path='/org/freedesktop/secrets'
        ))

        with open(__file__) as fh:
            print(await c.portal_call(
                'org.freedesktop.portal.Desktop',
                'OpenFile',
                ['', fh, {}],
            ))

        async with c.signal(
            'org.freedesktop.portal.Desktop', 'SettingChanged'
        ) as queue:
            async for value in queue:
                print(value)


if __name__ == '__main__':
    asyncio.run(amain())
