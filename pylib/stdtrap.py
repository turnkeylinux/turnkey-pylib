"""
Module that contains classes for capturing stdout/stderr.

Warning: if you aren't careful, exceptions raised after trapping stdout/stderr
will cause your program to exit silently.

StdTrap usage:


    trap = StdTrap()
    try:
        expression
    finally:
        trap.close()

    trapped_stdout = trap.stdout.read()
    trapped_stderr = trap.stderr.read()

UnitedStdTrap usage:

    trap = UnitedStdTrap()
    try:
        expression
    finally:
        trap.close()

    trapped_output = trap.std.read()

"""

import os
import sys
import pty
import errno
import select
from StringIO import StringIO

import thread
import time

class Error(Exception):
    pass

class PatchedReader:
    """Wrapper around the reader we get back from fdopen that fixes
    the exception raised when we try to read from a pipe that hasn't been
    written to."""
    
    def __init__(self, reader):
        self.reader = reader

    def read(self, size=None):
        try:
            if size is None:
                ret = self.reader.read()
            else:
                ret = self.reader.read(size)

            return ret
        except IOError, e:
            if e[0] == errno.EIO:
                return ""
        
    def __getattr__(self, name):
        return getattr(self.reader, name)
    
class StdTrap:
    def __init__(self, stdout=True, stderr=True, usepty=False, transparent=False):
        self.usepty = pty
        self.transparent = transparent
        
        if stdout:
            sys.stdout.flush()
            self.stdout_lock, self.stdout_buf, self.stdout_dupfd = self.trapfd(sys.stdout.fileno())
            self.trap_stdout = True
        else:
            self.trap_stdout = False

        if stderr:
            sys.stderr.flush()
            self.stderr_lock, self.stderr_buf, self.stderr_dupfd = self.trapfd(sys.stderr.fileno())
            self.trap_stderr = True
        else:
            self.trap_stderr = False

        self.stdout = None
        self.stderr = None

    def trapfd(self, orig_fd):
        # duplicate the fd we want to trap for safe keeping
        dup_fd = os.dup(orig_fd)

        # create a bi-directional pipe/pty
        # data written to w can be read from r
        if self.usepty:
            r, w = os.openpty()
        else:
            r, w = os.pipe()

        # swap w in place of the trapped fd
        # (this overwrites fd with w)
        os.dup2(w, orig_fd)
        os.close(w)

        buf = StringIO()

        lock = thread.allocate_lock()
        lock.acquire()
        
        def splice():
            def os_write_all(fd, data):
                while data:
                    len = os.write(fd, data)
                    if len < 0:
                        raise Error("os.write error")
                    data = data[len:]

            p = select.poll()
            p.register(r, select.POLLIN | select.POLLHUP)

            while True:
                try:
                    events = p.poll()
                except select.error:
                    continue

                if not events:
                    continue

                mask = events[0][1]
                if mask & select.POLLIN:
                    data = os.read(r, 4096)
                    buf.write(data)

                    if self.transparent:
                        # if our dupfd file descriptor has been closed
                        # redirect output to the originally trapped fd
                        try:
                            os_write_all(dup_fd, data)
                        except OSError, e:
                            if e[0] == errno.EBADF:
                                os_write_all(orig_fd, data)
                            else:
                                raise

                elif mask & select.POLLHUP:
                    break

            os.close(r)
            lock.release()
            
        thread.start_new_thread(splice, ())
        return lock, buf, dup_fd

    def restorefd(self, fd, dupfd):
        os.dup2(dupfd, fd)
        os.close(dupfd)

    def close(self):
        if self.trap_stdout:
            sys.stdout.flush()
            self.restorefd(sys.stdout.fileno(), self.stdout_dupfd)
            self.stdout_lock.acquire()
            self.stdout = StringIO(self.stdout_buf.getvalue())

        if self.trap_stderr:
            sys.stderr.flush()
            self.restorefd(sys.stderr.fileno(), self.stderr_dupfd)
            self.stderr_lock.acquire()
            self.stderr = StringIO(self.stderr_buf.getvalue())

class UnitedStdTrap(StdTrap):
    def __init__(self, usepty=False, transparent=False):
        self.usepty = usepty
        self.transparent = transparent
        
        sys.stdout.flush()
        self.stdout_lock, self.stdout_buf, self.stdout_dupfd = self.trapfd(sys.stdout.fileno())

        sys.stderr.flush()
        self.stderr_dupfd = os.dup(sys.stderr.fileno())
        os.dup2(sys.stdout.fileno(), sys.stderr.fileno())

        self.stderr_orig = sys.stderr
        self.std = self.stdout = self.stderr = None

    def close(self):
        sys.stdout.flush()
        self.restorefd(sys.stdout.fileno(), self.stdout_dupfd)

        sys.stderr.flush()
        self.restorefd(sys.stderr.fileno(), self.stderr_dupfd)

        self.stdout_lock.acquire()
        self.std = self.stdout = StringIO(self.stdout_buf.getvalue())

def silence(callback, args=()):
    """convenience function - traps stdout and stderr for callback.
    Returns (ret, trapped_output)
    """
    
    trap = UnitedStdTrap()
    try:
        ret = callback(*args)
    finally:
        trap.close()

    return ret

def getoutput(callback, args=()):
    trap = UnitedStdTrap()
    try:
        callback(*args)
    finally:
        trap.close()

    return trap.std.read()

def test(transparent=False):
    def sysprint():
        os.system("echo echo stdout")
        os.system("echo echo stderr 1>&2")

    trap1 = UnitedStdTrap(transparent=transparent)
    trap2 = UnitedStdTrap(transparent=transparent)
    print "hello world"
    trap2.close()
    print "trap2: " + trap2.std.read(),
    trap1.close(),
    print "trap1: " + trap1.std.read(),

    print "---"

    s = UnitedStdTrap(transparent=transparent)
    print "printing to united stdout..."
    print >> sys.stderr, "printing to united stderr..."
    sysprint()
    s.close()

    print 'trapped united stdout and stderr: """%s"""' % s.std.read()
    print >> sys.stderr, "printing to stderr"

    print "---"

    s = None
    s = UnitedStdTrap(transparent=transparent)
    print "printing to united stdout..."
    print >> sys.stderr, "printing to united stderr..."
    sysprint()
    s.close()

    print 'trapped united stdout and stderr: """%s"""' % s.std.read()
    print >> sys.stderr, "printing to stderr"

    print "---"
    
    s = StdTrap(transparent=transparent)
    s.close()
    print 'nothing in stdout: """%s"""' % s.stdout.read()
    print 'nothing in stderr: """%s"""' % s.stderr.read()

    print "---"

    s = StdTrap(transparent=transparent)
    print "printing to stdout..."
    print >> sys.stderr, "printing to stderr..."
    sysprint()
    s.close()

    print 'trapped stdout: """%s"""' % s.stdout.read()
    print >> sys.stderr, 'trapped stderr: """%s"""' % s.stderr.read()


if __name__ == '__main__':
     test(False)
     print
     print "=== TRANSPARENT MODE ==="
     print
     test(True)
