import unittest
from unittest.mock import ANY

from xibus import DBusError
from xibus import get_client


class TestCall(unittest.IsolatedAsyncioTestCase):
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
            self.assertIn('org.freedesktop.DBus', response)

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

    async def test_proxy_call(self):
        async with get_client('session') as client:
            response = await client.bus.call('ListNames', (), '')
            self.assertIn('org.freedesktop.DBus', response)

    async def test_magic_call(self):
        async with get_client('session') as client:
            response = await client.call(
                'org.freedesktop.DBus', None, None, 'ListNames', ()
            )
            self.assertIn('org.freedesktop.DBus', response)


class TestProperties(unittest.IsolatedAsyncioTestCase):
    async def test_get_property(self):
        async with get_client('session') as client:
            response = await client.get_property(
                'org.freedesktop.DBus',
                '/org/freedesktop/DBus',
                'org.freedesktop.DBus',
                'Features',
            )
            self.assertIn('ActivatableServicesChanged', response)

    async def test_get_property_error(self):
        async with get_client('session') as client:
            with self.assertRaises(DBusError) as ctx:
                await client.get_property(
                    'org.freedesktop.DBus',
                    '/org/freedesktop/DBus',
                    'org.freedesktop.DBus',
                    'DoesNotExist',
                )
            self.assertEqual(
                str(ctx.exception), 'org.freedesktop.DBus.Error.UnknownProperty'
            )

    async def test_proxy_get_property(self):
        async with get_client('session') as client:
            response = await client.bus.get_property('Features')
            self.assertIn('ActivatableServicesChanged', response)


class TestSignals(unittest.IsolatedAsyncioTestCase):
    async def test_subscribe_signal(self):
        async with get_client('session') as client:
            async with client.bus.subscribe_signal('NameOwnerChanged') as queue:
                async with client.acquire_name('xibus.test'):
                    pass

                i = aiter(queue)
                self.assertEqual(await anext(i), ('xibus.test', '', ANY))
                self.assertEqual(await anext(i), ('xibus.test', ANY, ''))
