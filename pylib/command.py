"A convenient interface for controlling commands"

import os
import signal
import time
import select
import re
import sys
import popen4
from fifobuffer import FIFOBuffer
from fileevent import *

def mkarg(x):
    """escape an argument from shell meta characters"""
    if '\'' not in x:
        return ' \'' + x + '\''
    s = ' "'
    for c in x:
        if c in '\\$"`':
            s = s + '\\'
        s = s + c
    s = s + '"'
    return s

def pid_free(pid):    
    try:
        retval = os.waitpid(pid, os.WNOHANG)
        if retval[0] == pid:
            return retval[1]
    except:
        return
    try:
        os.kill(pid, signal.SIGKILL)
        retval = os.waitpid(pid, 0)
        if retval[0] == pid:
            return retval[1]
    except:
        return None

    
def set_blocking(fd, block):
    import fcntl
    arg = os.O_NONBLOCK
    if block:
        arg =~ arg
    fcntl.fcntl(fd, fcntl.F_SETFL, arg)

class Command:
    """Convenience module for executing a command
    Usage:

    c = Command("./test.py")
    if c.state() == c.STATE_RUNNING:
        c.wait()

    print c.output()

    c = Command("./test.py")
    while c.output() is None:
        time.sleep(1)

    print "output = '%s', exitcode = %d" % (c.output(), c.exitcode())

    GOTCHA: if observeOutput=True, the caller must verify that the command
    has finished with the status() command or Command will leak open
    file descriptors.
    
    """
    STATE_RUNNING = 0
    STATE_FINISHED = 1
    STATE_TERMINATED = -1

    class Error(Exception):
        pass

    class _ChildObserver(Observer):
        def __init__(self, command):
            self.command = command

        def notify(self, subject, event, val):

            if event in ('read', 'readline'):
                self.command._dlog("# EVENT '%s':\n%s" % (event, val))
                self.command._output.write(val)
            elif event in ('readlines', 'xreadlines'):
                self.command._dlog("# EVENT '%s':\n%s" % (event, "".join(val)))
                self.command._output.write("".join(val))

    def __init__(self, cmd, runas=None, pty=False, setpgrp=False, debug=False, observeOutput=False):
        """Args:
        'cmd' what command to execute
            Can be a list ("/bin/ls", "-la")
            or a string "/bin/ls" (will be passed to sh -c)

        'pty' do we allocate a pty for command?
        'runas' user we run as (set user, set groups, etc.)
        'setpgrp' do we setpgrp in child? (create its own process group)
        """
        
        self._child = popen4.Popen4(cmd, 0, pty, runas, setpgrp)
        self.pid = self._child.pid

        self._setpgrp = setpgrp
        self._debug = debug
        self._cmd = cmd
        self._state = Command.STATE_RUNNING
        self._exitcode = None
        
        self._output = FIFOBuffer()

        if observeOutput:
            self._child.fromchild = FileEventAdaptor(self._child.fromchild)
            self._child.fromchild.addObserver(self._ChildObserver(self))
        self.observeOutput = observeOutput
        
        self._dlog("# command started (pid=%d, pty=%s): %s" % (self._child.pid,
                                                               `pty`,
                                                               cmd))

    def __del__(self):
        pid_free(self._child.pid)
        
    def _dlog(self, msg):
        if self._debug:
            print >> sys.stderr, msg
        
    def terminate(self, gracetime=0, sig=signal.SIGTERM):
        """terminate command. kills command with 'sig', then sleeps for 'gracetime', before sending SIGKILL
        """

        if self.status() == Command.STATE_RUNNING:
            pid = self.pid
            if self._setpgrp:
                pid = -pid

            os.kill(pid, sig)
            time.sleep(gracetime)
            if self.status() != Command.STATE_FINISHED:
                pid_free(pid)
                self._dlog("# command (pid %d) terminated" % self._child.pid)
                self._state = Command.STATE_TERMINATED

    def status(self):
        """return the status of the command:
        STATE_RUNNING		Command still running
        STATE_FINISHED		Command finished (or handled termination gracefully)
        STATE_TERMINATED	Command terminated
        """
        if self._state != Command.STATE_RUNNING:
            return self._state

        if self._child.poll() == -1:
            return Command.STATE_RUNNING

        self._dlog("# command (pid %d) finished" % self._child.pid)
        self._state = Command.STATE_FINISHED

        return self._state

    def free(self):
        """Free cyclical reference after we finish the command"""
        if self.observeOutput:
            self._child.fromchild.delObserversAll()

    def exitcode(self):
        """return the command's exitcode"""
        if self._exitcode is not None:
            return self._exitcode

        if self.status() != Command.STATE_FINISHED:
            return None

        self._exitcode = self._child.poll() >> 8
        return self._exitcode

    def wait(self, timeout=0, interval=0.2):
        """wait for process to finish executing.
        'timeout' is how long we wait (in seconds)
        'interval' is how long we sleep between checks to see if process has finished
        return value: did the process finish? True/False

        """
        if self.status() == Command.STATE_FINISHED:
            return True
        
        if timeout == 0:
            self._child.wait()
            return True
        else:
            start=time.time()
            while time.time() - start < timeout:
                if self.status() == Command.STATE_FINISHED:
                    return True
                time.sleep(interval)
            return False

    def output(self):
        """return the command's output as a string

        LIMITATIONS: unless we are using outputsearch, output will be empty until the command finished.
        """
        assert self.observeOutput == True
        
        if len(self._output):
            return self._output.getvalue()
        
        if self.status() != Command.STATE_FINISHED:
            return None

        self._child.fromchild.read()
        return self._output.getvalue()

    def outputfh(self):
        """return the command's filehandler.

        NOTE: this file handler magically updates self._output"""
        return self._child.fromchild
        
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
          You can check the status() to see if the process is still running.
        - Output is collected and can be accessed by the output() method [*]
        """
        assert self.observeOutput == True
        
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
        
        fh = self.outputfh()

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
        
class CommandTrue:
    """
    Simplified interface to Command class.
    
    A command istrue() if its exitcode == 0
    """
    def __init__(self, cmd):
        self._c = Command(cmd, observeOutput=False)
        self._istrue = None

    def wait(self, timeout=0):
        return self._c.wait(timeout)

    def terminate(self):
        self._c.terminate()

    def istrue(self):
        if self._istrue is not None:
            return self._istrue
        
        exitcode = self._c.exitcode()
        if exitcode is None:
            return None

        if exitcode:
            self._istrue = False
        else:
            self._istrue = True

        return self._istrue

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
    last_output = c.output()
    last_exitcode = c.exitcode()
    return c.exitcode() == 0

def output(cmd):
    """convenience function
    execute 'cmd' and return it's output

    Side effect: sets command.last_exitcode and command.last_output

    """
    global last_output
    global last_exitcode

    c = Command(cmd)
    c.wait()
    last_output = c.output()
    last_exitcode = c.exitcode()
    return c.output()
