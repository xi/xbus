import os
import asyncio
import socket

from message import marshal_method_call
from message import unmarshal_msg

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect('/run/user/1000/bus')

try:
    sock.send(b'\0')
    uid = os.getuid()
    uid_encoded = str(uid).encode('ascii').hex()
    sock.send(f'AUTH EXTERNAL {uid_encoded}\r\n'.encode('ascii'))
    assert sock.recv(128).startswith(b'OK')
    sock.send(b'NEGOTIATE_UNIX_FD\r\n')
    assert sock.recv(128).startswith(b'AGREE_UNIX_FD')
    sock.send(b'BEGIN\r\n')
    sock.send(marshal_method_call(0, 1, 'org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus', 'Hello', ('', [])))
    print(unmarshal_msg(sock.recv(1024)))
finally:
    sock.shutdown(socket.SHUT_RDWR)
