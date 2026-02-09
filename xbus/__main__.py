import asyncio

from . import get_client


async def amain():
    async with get_client('session') as c:
        print(await c.call(
            'org.freedesktop.portal.Desktop',
            None,
            None,
            'ReadOne',
            ('org.freedesktop.appearance', 'color-scheme'),
        ))
        print(await c.call(
            'org.freedesktop.DBus',
            None,
            None,
            'ListNames',
        ))
        async for path in c.iter_paths('org.freedesktop.secrets'):
            print(path)
        print(await c.get_property(
            'org.freedesktop.secrets',
            '/org/freedesktop/secrets',
            None,
            'Collections',
        ))

        with open(__file__) as fh:
            print(await c.portal_call(
                'org.freedesktop.portal.Desktop',
                None,
                None,
                'OpenFile',
                ['', fh, {}],
            ))

        async with c.signal(
            'org.freedesktop.portal.Desktop', None, None, 'SettingChanged'
        ) as queue:
            async for value in queue:
                print(value)


if __name__ == '__main__':
    asyncio.run(amain())
