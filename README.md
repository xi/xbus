# xibus - pure python async D-Bus library

This is a pure python implementation of the [D-Bus
Specification](https://dbus.freedesktop.org/doc/dbus-specification.html).
It consists of the following parts:

-   `marshal.py` implements the low-level wire format
-   `message.py` builds on that to define messages
-   `connection.py` allows to send and receive messages over a socket as well as introducing the concepts of method calls and signals
-   `client.py` provides high level abstractions
    -   properties
    -   introspection
    -   guessing the correct path and interface to reduce verbosity
    -   portal-style async responses (`org.freedesktop.portal.Request`)

## Usage

```python
import asyncio
from xibus import get_client

async def amain():
    async with get_client('session') as c:
        # call a method
        print(await c.call(
            'org.freedesktop.portal.Desktop',
            '/org/freedesktop/portal/desktop',
            'org.freedesktop.portal.Settings',
            'ReadOne',
            ('org.freedesktop.appearance', 'color-scheme'),
            'ss',
        ))

        # if path, interface, or signature are omitted,
        # they will be inferred from introspection
        print(await c.call(
            'org.freedesktop.portal.Desktop',
            None,
            None,
            'ReadOne',
            ('org.freedesktop.appearance', 'color-scheme'),
        ))

        # get a property
        print(await c.get_property(
            'org.freedesktop.portal.Desktop',
            None,
            'org.freedesktop.portal.Settings',
            'version',
        ))

        # receive signals
        async with c.subscribe_signal(
            'org.freedesktop.portal.Desktop',
            None,
            None,
            'SettingChanged',
        ) as queue:
            async for signal in queue:
                print(signal)

        # desktop portals have a different mechanism for returning values,
        # so there is a special way to call them
        await c.portal_call(
            'org.freedesktop.portal.Desktop',
            None,
            None,
            'OpenURI',
            ['', 'https://example.com', {}],
        )

asyncio.run(amain())
```

## Links

-   [dbus-next](https://github.com/altdesktop/python-dbus-next) and its forks
    [dbus-fast](https://github.com/bluetooth-devices/dbus-fast) and
    [asyncdbus](https://github.com/M-o-a-T/asyncdbus) also implements D-Bus in
    python, but the code is much more complex.
-   [Talk on why systemd is moving from D-Bus to
    Varlink](https://mirror.as35701.net/video.fosdem.org/2026/ub2147/NFNKEK-varlink-ipc-system-keynote.av1.webm)
