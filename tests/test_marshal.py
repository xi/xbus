import unittest

from xibus.message import Msg
from xibus.message import MsgFlag
from xibus.message import MsgType

MESSAGES = [
    {
        'message': Msg(
            MsgType.METHOD_CALL,
            1,
            destination='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            iface='org.freedesktop.DBus',
            member='Hello',
            sig='',
        ),
        'data': bytes.fromhex(
            '6c01000100000000010000006d00000001016f00150000002f6f72672f667265'
            '656465736b746f702f4442757300000002017300140000006f72672e66726565'
            '6465736b746f702e4442757300000000030173000500000048656c6c6f000000'
            '06017300140000006f72672e667265656465736b746f702e4442757300000000'
        ),
    },
    {
        'message': Msg(
            MsgType.METHOD_CALL,
            1,
            destination='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            iface='org.freedesktop.DBus',
            member='Hello',
            sig='as',
            body=(['hello', 'world'],),
        ),
        'data': bytes.fromhex(
            '6c0100011a000000010000007800000001016f00150000002f6f72672f667265'
            '656465736b746f702f4442757300000002017300140000006f72672e66726565'
            '6465736b746f702e4442757300000000030173000500000048656c6c6f000000'
            '06017300140000006f72672e667265656465736b746f702e4442757300000000'
            '0801670002617300160000000500000068656c6c6f00000005000000776f726c'
            '6400'
        ),
    },
    {
        'message': Msg(
            MsgType.METHOD_CALL,
            1,
            destination='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            iface='org.freedesktop.DBus',
            member='Hello',
            sig='a(uu)',
            body=([(1, 1), (2, 2)],),
        ),
        'data': bytes.fromhex(
            '6c01000118000000010000007b00000001016f00150000002f6f72672f667265'
            '656465736b746f702f4442757300000002017300140000006f72672e66726565'
            '6465736b746f702e4442757300000000030173000500000048656c6c6f000000'
            '06017300140000006f72672e667265656465736b746f702e4442757300000000'
            '0801670005612875752900000000000010000000000000000100000001000000'
            '0200000002000000'
        ),
    },
    {
        'message': Msg(
            MsgType.METHOD_CALL,
            1,
            destination='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            iface='org.freedesktop.DBus',
            member='Hello',
            sig='a{ss}',
            body=({'foo': 'bar', 'bat': 'baz'},),
        ),
        'data': bytes.fromhex(
            '6c01000128000000010000007b00000001016f00150000002f6f72672f667265'
            '656465736b746f702f4442757300000002017300140000006f72672e66726565'
            '6465736b746f702e4442757300000000030173000500000048656c6c6f000000'
            '06017300140000006f72672e667265656465736b746f702e4442757300000000'
            '0801670005617b73737d000000000000200000000000000003000000666f6f00'
            '030000006261720003000000626174000300000062617a00'
        ),
    },
    {
        'message': Msg(
            MsgType.METHOD_CALL,
            1,
            destination='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            iface='org.freedesktop.DBus',
            member='Hello',
            sig='a(as(uu(a{ss})))',
            body=(
                [
                    (['hello', 'there'], (5, 6, ({'five': 'six', 'seven': 'eight'},))),
                    (
                        ['to', 'the', 'world'],
                        (7, 8, ({'seven': 'eight', 'nine': 'ten'},)),
                    ),
                ],
            ),
        ),
        'data': bytes.fromhex(
            '6c010001c4000000010000008600000001016f00150000002f6f72672f667265'
            '656465736b746f702f4442757300000002017300140000006f72672e66726565'
            '6465736b746f702e4442757300000000030173000500000048656c6c6f000000'
            '06017300140000006f72672e667265656465736b746f702e4442757300000000'
            '08016700106128617328757528617b73737d292929000000bc00000000000000'
            '160000000500000068656c6c6f00000005000000746865726500000000000000'
            '05000000060000002e0000000000000004000000666976650000000003000000'
            '736978000000000005000000736576656e000000050000006569676874000000'
            '1a00000002000000746f0000030000007468650005000000776f726c64000000'
            '07000000080000002c0000000000000005000000736576656e00000005000000'
            '6569676874000000040000006e696e65000000000300000074656e00'
        )
    },
    {
        'message': Msg(
            MsgType.METHOD_CALL,
            1,
            destination='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            iface='org.freedesktop.DBus',
            member='Hello',
            sig='t',
            body=(9007199254740988,),
        ),
        'data': bytes.fromhex(
            '6c01000108000000010000007700000001016f00150000002f6f72672f667265'
            '656465736b746f702f4442757300000002017300140000006f72672e66726565'
            '6465736b746f702e4442757300000000030173000500000048656c6c6f000000'
            '06017300140000006f72672e667265656465736b746f702e4442757300000000'
            '0801670001740000fcffffffffff1f00'
        ),
    },
    {
        'message': Msg(
            MsgType.METHOD_CALL,
            1,
            destination='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            iface='org.freedesktop.DBus',
            member='Hello',
            sig='x',
            body=(-9007199254740988,),
        ),
        'data': bytes.fromhex(
            '6c01000108000000010000007700000001016f00150000002f6f72672f667265'
            '656465736b746f702f4442757300000002017300140000006f72672e66726565'
            '6465736b746f702e4442757300000000030173000500000048656c6c6f000000'
            '06017300140000006f72672e667265656465736b746f702e4442757300000000'
            '0801670001780000040000000000e0ff'
        ),
    },
    {
        'message': Msg(
            MsgType.METHOD_CALL,
            1,
            destination='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            iface='org.freedesktop.DBus',
            member='Hello',
            sig='bnqiud',
            body=(
                True,
                -200,
                150,
                -20000,
                20000,
                9083492084.4444,
            ),
        ),
        'data': bytes.fromhex(
            '6c01000118000000010000007c00000001016f00150000002f6f72672f667265'
            '656465736b746f702f4442757300000002017300140000006f72672e66726565'
            '6465736b746f702e4442757300000000030173000500000048656c6c6f000000'
            '06017300140000006f72672e667265656465736b746f702e4442757300000000'
            '0801670006626e7169756400000000000100000038ff9600e0b1ffff204e0000'
            '228ea3b758eb0042'
        ),
    },
    {
        'message': Msg(
            MsgType.METHOD_CALL,
            1,
            destination='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            iface='org.freedesktop.DBus',
            member='Hello',
            sig='v',
            body=(('s', 'hello world'),),
        ),
        'data': bytes.fromhex(
            '6c01000114000000010000007700000001016f00150000002f6f72672f667265'
            '656465736b746f702f4442757300000002017300140000006f72672e66726565'
            '6465736b746f702e4442757300000000030173000500000048656c6c6f000000'
            '06017300140000006f72672e667265656465736b746f702e4442757300000000'
            '0801670001760000017300000b00000068656c6c6f20776f726c6400'
        ),
    },
    {
        'message': Msg(
            MsgType.METHOD_CALL,
            1,
            destination='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            iface='org.freedesktop.DBus',
            member='Hello',
            sig='v',
            body=(('v', ('s', 'hello')),),
        ),
        'data': bytes.fromhex(
            '6c01000112000000010000007700000001016f00150000002f6f72672f667265'
            '656465736b746f702f4442757300000002017300140000006f72672e66726565'
            '6465736b746f702e4442757300000000030173000500000048656c6c6f000000'
            '06017300140000006f72672e667265656465736b746f702e4442757300000000'
            '080167000176000001760001730000000500000068656c6c6f00'
        ),
    },
    {
        'message': Msg(
            MsgType.METHOD_CALL,
            1,
            destination='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            iface='org.freedesktop.DBus',
            member='Hello',
            sig='a{sv}',
            body=(
                {
                    'variant_key_1': ('s', 'variant_val_1'),
                    'variant_key_2': ('s', 'variant_val_2'),
                },
            ),
        ),
        'data': bytes.fromhex(
            '6c01000162000000010000007b00000001016f00150000002f6f72672f667265'
            '656465736b746f702f4442757300000002017300140000006f72672e66726565'
            '6465736b746f702e4442757300000000030173000500000048656c6c6f000000'
            '06017300140000006f72672e667265656465736b746f702e4442757300000000'
            '0801670005617b73767d0000000000005a000000000000000d00000076617269'
            '616e745f6b65795f31000173000000000d00000076617269616e745f76616c5f'
            '31000000000000000d00000076617269616e745f6b65795f3200017300000000'
            '0d00000076617269616e745f76616c5f3200'
        ),
    },
    {
        'message': Msg(
            MsgType.METHOD_CALL,
            1,
            destination='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            iface='org.freedesktop.DBus',
            member='Hello',
            sig='v',
            body=(('as', ['foo', 'bar']),),
        ),
        'data': bytes.fromhex(
            '6c01000118000000010000007700000001016f00150000002f6f72672f667265'
            '656465736b746f702f4442757300000002017300140000006f72672e66726565'
            '6465736b746f702e4442757300000000030173000500000048656c6c6f000000'
            '06017300140000006f72672e667265656465736b746f702e4442757300000000'
            '0801670001760000026173001000000003000000666f6f000300000062617200'
        ),
    },
    {
        'message': Msg(
            MsgType.METHOD_CALL,
            1,
            destination='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            iface='org.freedesktop.DBus',
            member='Hello',
            sig='vas',
            body=(('v', ('s', 'world')), ['bar']),
        ),
        'data': bytes.fromhex(
            '6c01000120000000010000007900000001016f00150000002f6f72672f667265'
            '656465736b746f702f4442757300000002017300140000006f72672e66726565'
            '6465736b746f702e4442757300000000030173000500000048656c6c6f000000'
            '06017300140000006f72672e667265656465736b746f702e4442757300000000'
            '08016700037661730000000000000000017600017300000005000000776f726c'
            '64000000080000000300000062617200'
        ),
    },
    {
        'message': Msg(
            MsgType.METHOD_CALL,
            1,
            destination='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            iface='org.freedesktop.DBus',
            member='Hello',
            sig='asbbasbb',
            body=(['hello', 'worl'], True, False, ['hello', 'worl'], True, False),
        ),
        'data': bytes.fromhex(
            '6c01000148000000010000007e00000001016f00150000002f6f72672f667265'
            '656465736b746f702f4442757300000002017300140000006f72672e66726565'
            '6465736b746f702e4442757300000000030173000500000048656c6c6f000000'
            '06017300140000006f72672e667265656465736b746f702e4442757300000000'
            '08016700086173626261736262000000150000000500000068656c6c6f000000'
            '04000000776f726c000000000100000000000000150000000500000068656c6c'
            '6f00000004000000776f726c000000000100000000000000'
        ),
    },
    {
        'message': Msg(
            MsgType.METHOD_CALL,
            1,
            destination='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            iface='org.freedesktop.DBus',
            member='Hello',
            sig='as',
            body=(['//doesntmatter/über'],),
        ),
        'data': bytes.fromhex(
            '6c0100011d000000010000007800000001016f00150000002f6f72672f667265'
            '656465736b746f702f4442757300000002017300140000006f72672e66726565'
            '6465736b746f702e4442757300000000030173000500000048656c6c6f000000'
            '06017300140000006f72672e667265656465736b746f702e4442757300000000'
            '080167000261730019000000140000002f2f646f65736e746d61747465722fc3'
            'bc62657200'
        ),
    },
    {
        'message': Msg(
            MsgType.METHOD_CALL,
            1,
            destination='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            iface='org.freedesktop.DBus',
            member='Hello',
            sig='an',
            body=([-1024],),
        ),
        'data': bytes.fromhex(
            '6c01000106000000010000007800000001016f00150000002f6f72672f667265'
            '656465736b746f702f4442757300000002017300140000006f72672e66726565'
            '6465736b746f702e4442757300000000030173000500000048656c6c6f000000'
            '06017300140000006f72672e667265656465736b746f702e4442757300000000'
            '0801670002616e000200000000fc'
        ),
    },
    {
        'message': Msg(
            MsgType.SIGNAL,
            707226,
            flags=MsgFlag.NO_REPLY_EXPECTED,
            sender=':1.4',
            path='/org/bluez/hci0/dev_D0_C2_4E_08_AB_57',
            iface='org.freedesktop.DBus.Properties',
            member='PropertiesChanged',
            sig='sa{sv}as',
            body=(
                'org.bluez.Device1',
                {
                    'RSSI': ('n', -86),
                    'ManufacturerData': (
                        'a{qv}',
                        {
                            117: (
                                'ay',
                                list(b'B\x04\x01\x01p\xd0\xc2N\x08\xabW\xd2\xc2N\x08\xabV\x01\x00\x00\x00\x00\x00\x00'),
                            )
                        },
                    ),
                },
                [],
            ),
        ),
        'data': bytes.fromhex(
            '6c040101780000009aca0a009500000001016f00250000002f6f72672f626c75'
            '657a2f686369302f6465765f44305f43325f34455f30385f41425f3537000000'
            '020173001f0000006f72672e667265656465736b746f702e444275732e50726f'
            '7065727469657300030173001100000050726f706572746965734368616e6765'
            '6400000000000000080167000873617b73767d61730000000701730004000000'
            '3a312e3400000000110000006f72672e626c75657a2e44657669636531000000'
            '5400000000000000040000005253534900016e00aaff0000100000004d616e75'
            '6661637475726572446174610005617b71767d00240000007500026179000000'
            '180000004204010170d0c24e08ab57d2c24e08ab560100000000000000000000'
        ),
        'marshal': False,
    },
]


class TestMarshal(unittest.TestCase):
    maxDiff = 1000

    def test_marshal(self):
        for i, item in enumerate(MESSAGES):
            msg = item['message']
            data = (item['data'], [])

            with self.subTest(i=i, action='unmarshal'):
                self.assertEqual((msg, b'', []), Msg.unmarshal(*data))

            # marshal output is not well defined (e.g. sorting)
            if item.get('marshal', True):
                with self.subTest(i=i, action='marshal'):
                    self.assertEqual(msg.marshal(), data)

    def test_invalid_signature(self):
        for sig in ['a(', 'a{yyy}', 'X']:
            msg = Msg(
                MsgType.METHOD_CALL,
                1,
                destination='org.freedesktop.DBus',
                path='/org/freedesktop/DBus',
                iface='org.freedesktop.DBus',
                member='Hello',
                sig=sig,
                body=(None,)
            )
            with self.subTest(sig=sig):
                with self.assertRaises(ValueError):
                    msg.marshal()

    def test_wrong_version(self):
        data = bytes.fromhex(
            '6c01000200000000010000006d00000001016f00150000002f6f72672f667265'
            '656465736b746f702f4442757300000002017300140000006f72672e66726565'
            '6465736b746f702e4442757300000000030173000500000048656c6c6f000000'
            '06017300140000006f72672e667265656465736b746f702e4442757300000000'
        )
        with self.assertRaises(ValueError):
            Msg.unmarshal(data, [])

    def test_remaining_data(self):
        data = MESSAGES[0]['data'] + b'\x00'
        _, tail, tail_fds = Msg.unmarshal(data, [1])
        self.assertEqual(tail, b'\x00')
        self.assertEqual(tail_fds, [1])
