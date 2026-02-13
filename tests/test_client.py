import unittest

from xibus import get_client
from xibus.connection import DBusError


class TestClient(unittest.IsolatedAsyncioTestCase):
    async def test_call(self):
        async with get_client('session') as client:
            response = await client.call(
                'org.freedesktop.DBus',
                '/org/freedesktop/DBus',
                'org.freedesktop.DBus',
                'ListNames',
                (),
                '',
            )
            self.assertEqual(response, ['org.freedesktop.DBus', ':1.0'])

    async def test_fail_on_double_hello(self):
        async with get_client('session') as client:
            with self.assertRaises(DBusError) as ctx:
                await client.call(
                    'org.freedesktop.DBus',
                    '/org/freedesktop/DBus',
                    'org.freedesktop.DBus',
                    'Hello',
                    (),
                    '',
                )
            self.assertEqual(str(ctx.exception), 'org.freedesktop.DBus.Error.Failed')
