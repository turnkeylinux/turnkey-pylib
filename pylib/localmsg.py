# Copyright (c) 2006 Liraz Siri <liraz@turnkeylinux.org>
#
# This file is part of turnkey-pylib.
#
# turnkey-pylib is open source software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.

"""Extremely simple message passing through unix socket mechanism"""

import socket
import os

SOCKPATH='/tmp/.localmsg'

class Server:
    """Very simple message passing mechanism."""
    def __init__(self,path=SOCKPATH):
        """starts listening on 'path;"""
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            os.unlink(path)
        except OSError:
            pass
        sock.bind(path)
        sock.listen(1)
        self._sock = sock

    def deliver(self, msg):
        """waits for connection and delivers message"""
        (c, addr) = self._sock.accept()
        c.sendall(msg)
        c.close()

def deliver(msg, path=SOCKPATH):
    """convenience routine: initializes Server on path, and waits for a connection to deliver a message
    """
    s = Server(path)
    s.deliver(msg)

class Error(Exception):
    pass

class Client:
    def __init__(self, path=SOCKPATH):
        self._path = path

    def receive(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(self._path)
        except socket.error, e:
            raise Error("can't connect to %s: %s" % (self._path, e[1]))

        fh = sock.makefile("r", 0)
        msg = fh.read()
        fh.close()
        sock.close()

        return msg

def receive(path=SOCKPATH):
    """receive message (function interface)"""
    c = Client(path)
    return c.receive()

