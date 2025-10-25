import asyncio
from contextlib import contextmanager

from gi.repository import Gio
from gi.repository import GLib

BUS_SESSION = Gio.BusType.SESSION
BUS_SYSTEM = Gio.BusType.SYSTEM


def glib_run_sync(fn):
    x = []
    loop = GLib.MainLoop()

    def done(result, error=None):
        x.append(result)
        x.append(error)
        loop.quit()

    fn(done)
    loop.run()
    if x[1]:
        raise x[1]
    return x[0]


async def glib_run(fn):
    return await asyncio.to_thread(glib_run_sync, fn)


@contextmanager
def glib_errors(done):
    try:
        yield
    except Exception as e:
        done(None, e)


async def dbus_call(bus, name, path, iface, method, params):
    # print(f'dbus_call("{name}", "{path}", "{iface}", "{method}")')
    def wrapper(done):
        def on_call(proxy, res):
            with glib_errors(done):
                result = proxy.call_finish(res)
                done(result)

        def on_proxy(_proxy, res):
            with glib_errors(done):
                proxy = _proxy.new_for_bus_finish(res)
                proxy.call(
                    method,
                    GLib.Variant(*params),
                    Gio.DBusCallFlags.NONE,
                    -1,
                    callback=on_call,
                )

        with glib_errors(done):
            Gio.DBusProxy.new_for_bus(
                bus,
                Gio.DBusProxyFlags.NONE,
                None,
                name,
                path,
                iface,
                callback=on_proxy,
            )
    return await glib_run(wrapper)
