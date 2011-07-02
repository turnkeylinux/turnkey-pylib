# Copyright (c) 2007-2011 Liraz Siri <liraz@turnkeylinux.org>
# 
# This file is part of turnkey-pylib.
# 
# turnkey-pylib is open source software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.

"A convenient interface for controlling commands"

import os
import signal
import time
import select
import re
import sys
import errno
import termios

import popen4
from fifobuffer import FIFOBuffer
from fileevent import *

from commands import mkarg

def fmt_argv(argv):
    if not argv:
        return ""

    args = argv[1:]

    for i, arg in enumerate(args):
        if re.search(r"[\s'\"]", arg):
            args[i] = mkarg(arg)
        else:
            args[i] = " " + arg

    return argv[0] + "".join(args)

def set_blocking(fd, block):
    import fcntl
    arg = os.O_NONBLOCK
    if block:
        arg =~ arg
    fcntl.fcntl(fd, fcntl.F_SETFL, arg)

class Command(object):
    """Convenience module for executing a command

    attribute notes::

        'exitcode' - None if the process hasn't exited, exitcode otherwise

        'output' - None if the process hasn't exited and fromchild hasn't
                   been accessed, the full output of the process

        'running' - True if process is still running, False otherwise

        'terminated' - Returns signal number if terminated, None otherwise

    Usage example::

        c = Command("./test.py")
        if c.running:
            c.wait()

        assert c.running is False

        print c.output

        c = Command("./test.py")

        # Unless you read from command.fromchild or use
        # command.outputsearch() command.output will be None until the
        # command finishes.

        while c.output is None: 
            time.sleep(1)

        print "output = '%s', exitcode = %d" % (c.output, c.exitcode)

        c = Command("cat", pty=True)
        print >> c.tochild, "test"
        print c.fromchild.readline(),

    """
    class Error(Exception):
        pass

    class _ChildObserver(Observer):
        def __init__(self, outputbuf, debug=False):
            self.debug = debug
            self.outputbuf = outputbuf

        def _dprint(self, event, msg):
            if self.debug:
                print >> sys.stderr, "# EVENT '%s':\n%s" % (event, msg)

        def notify(self, subject, event, val):
            if event in ('read', 'readline'):
                self._dprint(event, val)
                self.outputbuf.write(val)
            elif event in ('readlines', 'xreadlines'):
                self._dprint(event, "".join(val))
                self.outputbuf.write("".join(val))

    def __init__(self, cmd, runas=None, pty=False, setpgrp=False, debug=False):
        """Args:
        'cmd' what command to execute
            Can be a list ("/bin/ls", "-la")
            or a string "/bin/ls" (will be passed to sh -c)

        'pty' do we allocate a pty for command?
        'runas' user we run as (set user, set groups, etc.)
        'setpgrp' do we setpgrp in child? (create its own process group)
        """
        
        self._child = popen4.Popen4(cmd, 0, pty, runas, setpgrp)
        self.tochild = self._child.tochild
        self._fromchild = None

        self.pid = self._child.pid
        self.ppid = os.getpid()

        self._setpgrp = setpgrp
        self._debug = debug
        self._cmd = cmd
        
        self._output = FIFOBuffer()
        self._dprint("# command started (pid=%d, pty=%s): %s" % (self._child.pid,
                                                               `pty`,
                                                               cmd))

    def __del__(self):
        # don't terminate() a process we didn't start
        if os.getpid() == self.ppid:
            self.terminate()
        
    def _dprint(self, msg):
        if self._debug:
            print >> sys.stderr, msg
        
    def terminate(self, gracetime=0, sig=signal.SIGTERM):
        """terminate command. kills command with 'sig', then sleeps for 'gracetime', before sending SIGKILL
        """

        if self.running:
            if self._child.pty:
                cc_magic = termios.tcgetattr(self._child.tochild.fileno())[-1]
                ctrl_c = cc_magic[termios.VINTR]
                self._child.tochild.write(ctrl_c)

            pid = self.pid
            if self._setpgrp:
                pid = -pid

            try:
                os.kill(pid, sig)
            except OSError, e:
                if e[0] != errno.EPERM or \
                   not self._child.pty or \
                   not self.wait(timeout=6, interval=0.1):
                    raise

                return
            
            time.sleep(gracetime)

            if self.running:
                os.kill(pid, signal.SIGKILL)

                if not self.wait(timeout=3, interval=0.1):
                    raise self.Error("process just won't die!")

                self._dprint("# command (pid %d) terminated" % self._child.pid)

    def terminated(self):
        status = self._child.poll()

        if not os.WIFSIGNALED(status):
            return None
        
        return os.WTERMSIG(status)
    terminated = property(terminated)

    def running(self):
        if self._child.poll() == -1:
            return True

        return False
    running = property(running)

    def exitcode(self):
        if self.running:
            return None

        status = self._child.poll()

        if not os.WIFEXITED(status):
            return None

        return os.WEXITSTATUS(status)
    exitcode = property(exitcode)

    def wait(self, timeout=0, interval=0.2):
        """wait for process to finish executing.
        'timeout' is how long we wait (in seconds)
        'interval' is how long we sleep between checks to see if process has finished
        return value: did the process finish? True/False

        """
        if not self.running:
            return True
        
        if timeout == 0:
            self._child.wait()
            return True
        else:
            start=time.time()
            while time.time() - start < timeout:
                if not self.running:
                    return True
                time.sleep(interval)

            return False

    def output(self):
        if len(self._output):
            return self._output.getvalue()
        
        if self.running:
            return None

        # this will read into self._output via _ChildObserver
        self.fromchild.read() 

        return self._output.getvalue()

    output = property(output)

    def fromchild(self):
        """return the command's filehandler.

        NOTE: this file handler magically updates self._output"""

        if self._fromchild:
            return self._fromchild

        self._fromchild = FileEventAdaptor(self._child.fromchild)
        self._fromchild.addObserver(self._ChildObserver(self._output,
                                                        self._debug))
        return self._fromchild

    fromchild = property(fromchild)
        
    def outputsearch(self, p, timeout=0, linemode=False):
        """Search for 'p' in the command's output, while listening for more output from command, within 'timeout'

        'p' can be a list of re patterns or a single re pattern
           the value of a pattern can be an re string, or a compiled re object
        If 'timeout' is 0, wait forever [*]

	'linemode' determines whether we search output line by line (as it comes), or all of the output in aggregate
        
        Return value:
        Did we match the output?
            Return a tuple (the pattern we matched, the string match)
        Otherwise (timeout/HUP) Return empty tuple ()

        Side effects:
        - If we HUP, we wait for the process to finish.
          You can check if the process is still running.

        - Output is collected and can be accessed by the output attribute [*]
        """
        
        patterns = []
        if not type(p) in (tuple, list):
            patterns.append(p)
        else:
            patterns += p

        # compile all patterns into re objects, but keep the original pattern object
        # so we can return it to the user when we match (friendlier interface)
        re_type = type(re.compile(""))
        for i in xrange(len(patterns)):
            if type(patterns[i]) is not re_type:
                patterns[i] = (re.compile(patterns[i]), patterns[i])
            else:
                patterns[i] = (patterns[i], patterns[i])

        def check_match():
            if linemode:
                while 1:
                    line = self._output.readline(True)
                    if not line:
                        return None
                    
                    for pattern_re, pattern_orig in patterns:
                        match = pattern_re.search(line)
                        if match:
                            return pattern_orig, match

                    if not line.endswith('\n'):
                        return None
                        
            else:
                # match against the entire buffered output
                for pattern_re, pattern_orig in patterns:
                    match = pattern_re.search(self._output.getvalue())
                    if match:
                        return pattern_orig, match
            
        # maybe we already match? (in buffered output)
        m = check_match()
        if m:
            return m
        
        fh = self.fromchild

        def handle_events(poll_events):
            fd, mask = poll_events[0]
            if mask & select.POLLIN:
                fh.read()
                match = check_match()
                if match:
                    return match

            if mask & select.POLLHUP:
                self.wait()
                return ()

        def poll_for_new_output():
            p = select.poll()
            p.register(fh.fileno(), select.POLLIN | select.POLLHUP)
            
            started = time.time()
            if timeout:
                while time.time() - started < timeout:
                    time_elapsed = time.time() - started
                    try:
                        events = p.poll(timeout - time_elapsed)
                    except select.error:
                        continue
                    if events:
                        ret = handle_events(events)
                        if ret is not None:
                            return ret
            else:
                while 1:
                    try:
                        events = p.poll()
                    except select.error:
                        continue
                    if events:
                        ret = handle_events(events)
                        if ret is not None:
                            return ret

            return None

        set_blocking(fh.fileno(), 0)
        ret = poll_for_new_output()
        try:
            set_blocking(fh.fileno(), 1)
        except:
            pass

        return ret

    def __repr__(self):
        return "Command(%s)" % `self._cmd`

    def __str__(self):
        if isinstance(self._cmd, str):
            return self._cmd

        return fmt_argv(self._cmd)
        
class CommandTrue:
    """
    Simplified interface to Command class.
    
    A command istrue() if its exitcode == 0
    """
    def __init__(self, cmd):
        self._c = Command(cmd)

    def wait(self, timeout=0):
        return self._c.wait(timeout)

    def terminate(self):
        self._c.terminate()

    def istrue(self):
        exitcode = self._c.exitcode
        if exitcode is None:
            return None

        if exitcode:
            return False
        else:
            return True

last_exitcode = None
last_output = None

def eval(cmd, setpgrp=False):
    """convenience function
    execute 'cmd' and return True/False is exitcode == 0

    Side effect: sets command.last_exitcode and command.last_output
    """
    global last_output
    global last_exitcode
    
    c = Command(cmd, setpgrp=setpgrp)
    c.wait()
    last_output = c.output
    last_exitcode = c.exitcode
    return last_exitcode == 0

def output(cmd):
    """convenience function
    execute 'cmd' and return it's output

    Side effect: sets command.last_exitcode and command.last_output

    """
    global last_output
    global last_exitcode

    c = Command(cmd)
    c.wait()
    last_output = c.output
    last_exitcode = c.exitcode

    return last_output
