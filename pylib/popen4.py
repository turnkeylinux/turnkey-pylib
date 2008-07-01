import sys
import os
import termios
import pty
import signal
import pwd
import grp

_active = []

try:
    MAXFD = os.sysconf('SC_OPEN_MAX')
except (AttributeError, ValueError):
    MAXFD = 256

SHELL = os.environ.get('SHELL', '/bin/sh')

def _cleanup():
    for inst in _active[:]:
        inst.poll()

class CatchIOErrorWrapper:
    """wraps around a file handler and catches IOError exceptions"""

    def __init__(self, fh):
        self.fh  = fh

    def __del__(self):
        try:
            self.fh.close()
        except IOError:
            pass

    def __getattr__(self, attr):
        return getattr(self.fh, attr)
        
    def read(self, size=-1):
        try:
            return self.fh.read(size)
        except IOError:
            return ''
            
    def readline(self, size=-1):
        try:
            return self.fh.readline(size)
        except IOError:
            return ''

    def readlines(self, size=-1):
        try:
            return self.fh.readlines(size)
        except IOError:
            return []

    def xreadlines(self):
        return self.fh.xreadlines()

class Popen4:
    """An implementation of popen2.Popen4 that can allocates a pty or a pipe for
    the executed command.

    Ptys are useful for cases where the unix buffering is going to ruin your day.
    
    """

    sts = -1

    def __init__(self, cmd, bufsize=0, pty=False, runas=None, setpgrp=False):
        """'runas' can be uid or username"""
        try:
            if runas is not None:
                uid = int(runas)
                runas = pwd.getpwuid(uid)[0]
        except ValueError:
            pass

        self.childerr = None
        if pty:
            self._init_pty(cmd, bufsize, runas, setpgrp)
        else:
            self._init_pipe(cmd, bufsize, runas, setpgrp)

        self.pty = pty
#        _active.append(self) # DEBUG TEST

    def _init_pty(self, cmd, bufsize, runas, setpgrp):
        def tty_echo_off(fd):
            new = termios.tcgetattr(fd)
            new[3] = new[3] & ~termios.ECHO          # lflags
            termios.tcsetattr(fd, termios.TCSANOW, new)

        (pid, fd) = pty.fork()
        if not pid:
            # Child
            if setpgrp:
                os.setpgrp()
            if runas is not None:
                self._drop_privileges(runas)
            self._run_child(cmd)

        tty_echo_off(fd)
        
        self.pid = pid
        self.fromchild = CatchIOErrorWrapper(os.fdopen(fd, "r+", bufsize))
        self.tochild = self.fromchild

    def _init_pipe(self, cmd, bufsize, runas, setpgrp):
        p2cread, p2cwrite = os.pipe()
        c2pread, c2pwrite = os.pipe()
        self.pid = os.fork()
        if self.pid == 0:
            # Child
            if setpgrp:
                os.setpgrp()
            if runas is not None:
                self._drop_privileges(runas)
            os.dup2(p2cread, 0)
            os.dup2(c2pwrite, 1)
            os.dup2(c2pwrite, 2)
            
            self._run_child(cmd)
        os.close(p2cread)
        self.tochild = os.fdopen(p2cwrite, 'w', bufsize)
        os.close(c2pwrite)
        self.fromchild = os.fdopen(c2pread, 'r', bufsize)

    def _run_child(self, cmd):
        if isinstance(cmd, basestring):
            cmd = [SHELL, '-c', cmd]
        for i in range(3, MAXFD):
            try:
                os.close(i)
            except OSError:
                pass
        try:
            os.execvp(cmd[0], cmd)
        finally:
            os._exit(1)
    
    def __del__(self):
        try:
            self.poll()
        except OSError:
            pass

        try:
            self.fromchild.close()
            self.tochild.close()
        except:
            pass
            
    def _drop_privileges(self, user):
        pwent = pwd.getpwnam(user)
        uid, gid, home = pwent[2], pwent[3], pwent[5]
        os.unsetenv("XAUTHORITY")
        os.putenv("USER", user)
        os.putenv("HOME", home)

        usergroups = []
        groups = grp.getgrall()
        for group in groups:
            if user in group[3]:
                usergroups.append(group[2])
        
        os.setgroups(usergroups)
        os.setgid(gid)
        os.setuid(uid)

    def poll(self):
        """Return the exit status of the child process if it has finished,
        or -1 if it hasn't finished yet."""
        if self.sts < 0:
            pid, sts = os.waitpid(self.pid, os.WNOHANG)
            if pid == self.pid:
                self.sts = sts

        return self.sts

    def wait(self):
        """Wait for and return the exit status of the child process."""
        pid, sts = os.waitpid(self.pid, 0)
        if pid == self.pid:
            self.sts = sts
#            _active.remove(self) # DEBUG TEST
        return self.sts
    
