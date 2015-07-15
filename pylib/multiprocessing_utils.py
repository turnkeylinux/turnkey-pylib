# Copyright (c) 2011-2015 Liraz Siri <liraz@turnkeylinux.org>
#
# This file is part of turnkey-pylib.
#
# turnkey-pylib is open source software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.

import signal

import time
from multiprocessing import Process, Event, Condition, Value
from multiprocessing.queues import Queue, Empty

from threadloop import ThreadLoop

class WaitableQueue(Queue):
    """Queue that uses a semaphore to reliably count items in it"""
    class Vacuum(ThreadLoop):
        def __init__(self, q, l):
            def callback():
                q.wait_notempty(0.1)

                while True:
                    try:
                        val = q.get(False)
                        l.append(val)

                    except Empty:
                        break

            ThreadLoop.__init__(self, callback)

    def __init__(self, maxsize=0):
        self.cond_empty = Condition()
        self.cond_notempty = Condition()
        self._put_counter = Value('i', 0)

        Queue.__init__(self, maxsize)

    def put(self, obj, block=True, timeout=None):
        Queue.put(self, obj, block, timeout)
        self._put_counter.value += 1

        if self.qsize() != 0:
            self.cond_notempty.acquire()
            try:
                self.cond_notempty.notify_all()
            finally:
                self.cond_notempty.release()

    @property
    def put_counter(self):
        return self._put_counter.value

    def get(self, block=True, timeout=None):
        ret = Queue.get(self, block, timeout)
        if self.qsize() == 0:
            self.cond_empty.acquire()
            try:
                self.cond_empty.notify_all()
            finally:
                self.cond_empty.release()

        return ret

    def wait_empty(self, timeout=None):
        """Wait for all items to be got"""
        self.cond_empty.acquire()
        try:
            if self.qsize():
                self.cond_empty.wait(timeout)
        finally:
            self.cond_empty.release()

    def wait_notempty(self, timeout=None):
        """Wait for all items to be got"""
        self.cond_notempty.acquire()
        try:
            if self.qsize() == 0:
                self.cond_notempty.wait(timeout)
        finally:
            self.cond_notempty.release()

class Deferred:
    def __init__(self, callable, *args, **kwargs):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        return self.callable(*self.args, **self.kwargs)

class Parallelize:
    """
    Usage:

    1) You pass a sequence of callables to Parallelize. In the most simple
       usage case these will be functions, but they can also be callable
       instances.

    2) You get back a Parallelize instance which is another callable, which
       you call with input arguments to queue a parallelized call in one of
       the underlying processes.

    3) The .wait() method waits for all queued execution to finish.

    4) The .stop() method stops parallel execution.

       Returns an empty array if you call it after wait() has completed.

       Returns aborted inputs if you call it mid-execution (e.g., handling an
       exception such as Ctrl-C)

    5) The .results is an iterator that iterates over return values from workers.

       A background thread collects return values in real-time as soon as the
       underlying functions in various processes finish executing and return
       values.

       After .wait() the number of return values will be the same size as the number of calls
       to the Parallelize instance, unless parallelize was aborted.

    Note that you have to call either wait or stop or Parallelize to collect results.

    Exception handling:

        An uncaught exception inside a worker kills the worker, resubmits the
        input into the queue where it will be picked up by another worker.

    """
    class Error(Exception):
        pass

    class Worker(Process):
        class Retry(Exception):
            pass

        class Terminated(Exception):
            pass

        @classmethod
        def worker(cls, initialized, done, idle, q_executors, q_input, q_output, executor):
            def raise_exception(s, f):
                signal.signal(s, signal.SIG_IGN)
                raise cls.Terminated

            signal.signal(signal.SIGTERM, raise_exception)
            signal.signal(signal.SIGINT, raise_exception)

            idle.clear()
            try:
                if isinstance(executor, Deferred):
                    executor = executor()
                    if not callable(executor):
                        raise Parallelize.Error("product of deferred executor %s is not callable" % `executor`)

                q_executors.put(executor)
                initialized.set()
            except cls.Terminated:
                return
            finally:
                idle.set()

            class UNDEFINED:
                pass

            try:
                while True:
                    if done.is_set():
                        return

                    retval = UNDEFINED
                    try:
                        input = q_input.get(timeout=0.1)
                    except Empty:
                        continue

                    idle.clear()

                    try:
                        if isinstance(input, tuple):
                            retval = executor(*input)
                        else:
                            retval = executor(input)
                        q_output.put(retval)

                    except cls.Retry:
                        q_input.put(input)

                    except: # uncaught exceptions destroy worker
                        if retval is UNDEFINED:
                            q_input.put(input)

                        raise

                    finally:
                        idle.set()

            except cls.Terminated:
                pass # just exit peacefully

        def __init__(self, q_executors, q_input, q_output, executor):
            self.initialized = Event()
            self.idle = Event()
            self.done = Event()

            self.idle.set()

            Process.__init__(self,
                             target=self.worker,
                             args=(self.initialized, self.done, self.idle, q_executors, q_input, q_output, executor))

        def is_busy(self):
            return self.is_alive() and not self.idle.is_set()

        def is_initialized(self):
            return self.initialized.is_set()

        def is_stopped(self):
            return self.done.is_set()

        def wait(self, timeout=None):
            """wait until Worker is idle"""
            return self.idle.wait(timeout)

        def stop(self):
            """let worker finish what it was doing and join"""
            if not self.is_alive():
                return

            self.done.set()

    class IterResults:
        def __init__(self, parent):
            self.parent = parent
            self.yielded = 0

        def __iter__(self):
            self.yielded = 0
            return self

        def next(self):
            finished = False

            while True:
                if len(self.parent._results) > self.yielded:
                    result = self.parent._results[self.yielded]
                    self.yielded += 1
                    return result

                if not finished:
                    finished = self.parent.wait(block=False)

                if finished and self.yielded == len(self.parent._results):
                    raise StopIteration

        def __len__(self):
            return len(self.parent._results)

        def __getitem__(self, key):
            return self.parent._results[key]

        def __repr__(self):
            return repr(self.parent._results)

    def __init__(self, executors):
        for executor in executors:
            if not callable(executor):
                raise self.Error("executor %s is not callable" % `executor`)

        q_input = WaitableQueue()
        q_output = WaitableQueue()
        q_executors = WaitableQueue()

        self.workers = []
        for executor in executors:
            worker = self.Worker(q_executors, q_input, q_output, executor)
            worker.start()

            self.workers.append(worker)

        self.size = len(executors)

        self.q_input = q_input
        self.q_executors = q_executors

        self._results = []
        self._results_vacuum = WaitableQueue.Vacuum(q_output, self._results)

        self.results = self.IterResults(self)
        self._executors = None

    @property
    def executors(self):
        if self._executors:
            return self._executors

        def finished_initialization():
            # returns 0 unless finished, else numbers of initialized workers
            executors = 0
            for worker in self.workers:
                if not worker.is_alive():
                    continue

                if not worker.is_initialized():
                    return 0

                executors += 1

            return executors

        while True:
            initialized = finished_initialization()
            if initialized:
                break

        self._executors = []
        for i in range(initialized):
            executor = self.q_executors.get()
            self._executors.append(executor)

        self.q_executors = None
        return self._executors

    def any_alive(self):
        """Return True if any workers are alive, else False"""
        for worker in self.workers:
            if worker.is_alive():
                return True

        return False

    def _wait_nonblock(self, keepalive=True, keepalive_spares=0):

        def find_busy_worker():
            for worker in self.workers:
                if not worker.is_alive() or worker.is_stopped():
                    continue

                if worker.is_initialized() and worker.is_busy():
                    return worker

        # gauntlet of checks to make sure the input queue is empty and all
        # workers are idle

        self.q_input.wait_empty(0.1)

        if not self.any_alive():
            return True

        saved_put_counter = self.q_input.put_counter

        if not keepalive:

            # if keepalive is False shutdown workers that aren't busy
            if self.q_input.qsize() != 0:
                return False

            idle_workers = [ worker for worker in self.workers
                                if worker.is_alive() and \
                                not worker.is_busy() and \
                                not worker.is_stopped() ]

            if len(idle_workers) > keepalive_spares:
                for worker in idle_workers:

                    # check is_busy() again just to make sure
                    if not worker.is_busy():
                        worker.stop()
                        break

                return False

            busy_worker = find_busy_worker()
            if busy_worker:
                time.sleep(0.1)
                return False

        else:
            worker = find_busy_worker()
            if worker:
                worker.wait()
                return False

        # give puts to the input Queue a chance to make it through
        time.sleep(0.1)

        # workers may have written to the input Queue
        if self.q_input.put_counter != saved_put_counter:
            return False

        return True

    def wait(self, keepalive=True, keepalive_spares=0, block=True):
        """wait for all input to be processed by workers.

        Returns True if finished (always True when block=True) else False

        Arguments:

        If keepalive=False: stop idle workers once there's nothing left to do.
        If keepalive=False and keepalive_spares > 0: keep alive at least
        keepalive_spares spare workers.

        """

        while True:

            finished = self._wait_nonblock(keepalive, keepalive_spares)
            if finished or not block:
                return finished

    def stop(self, finish_timeout=None):
        """Stop workers and return any unprocessed input values"""

        if not self.workers:
            return

        # ignore SIGINT and SIGTERM for now (restore later)
        sigint_handler = signal.getsignal(signal.SIGINT)
        sigterm_handler = signal.getsignal(signal.SIGTERM)

        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

        for worker in self.workers:
            worker.stop()

        aborted = []
        inputs_vacuum = WaitableQueue.Vacuum(self.q_input, aborted)

        started = time.time()

        try:
            while True:
                if not self.any_alive():
                    break

                if finish_timeout is not None and (time.time() - started) > finish_timeout:
                    break

                time.sleep(0.1)

            for worker in self.workers:
                if worker.is_alive():
                    worker.terminate()

            for worker in self.workers:
                if worker.is_alive():
                    worker.join()

            self.workers = []
        finally:
            time.sleep(0.1)
            inputs_vacuum.stop()

        self._results_vacuum.stop()

        signal.signal(signal.SIGINT, sigint_handler)
        signal.signal(signal.SIGTERM, sigterm_handler)

        return aborted

    def __call__(self, *args):
        if len(args) == 1:
            self.q_input.put(args[0])
        else:
            self.q_input.put(args)

    def __del__(self):
        self.stop()

def test():
    import time
    def sleeper(seconds):
        time.sleep(seconds)
        return seconds

    # pickle doesn't like embedded functions
    globals()[sleeper.__name__] = sleeper

    sleeper = Parallelize([ sleeper ] * 250)
    print "Allocated children"

    try:
        for i in range(1000):
            sleeper(1)

        print "Queued parallelized invocations. Ctrl-C to abort!"
        sleeper.wait()

        print "Finished waiting"

    finally:
        aborted = sleeper.stop()
        if aborted:
            print "len(aborted) = %d" % len(aborted)
            print "len(aborted) + len(results) = %d" % (len(aborted) + len(sleeper.results))

        print "len(pool.results) = %d" % len(sleeper.results)

def test2():
    class ExampleExecutor:
        def __init__(self, name):
            import os

            self.name = name
            self.pid = os.getpid()

            #import random
            # if we want to test what happens to failed initializations
            #if random.randint(0, 1):
            #    raise Exception

            print "%s.__init__: pid %d" % (self.name, self.pid)

        def __call__(self, *args):
            print "%s.__call__(%s)" % (self.name, `args`)
            return args

        def __del__(self):
            import os
            print "%s.__del__: self.pid=%d, os.getpid=%d" % (self.name, self.pid, os.getpid())

    # pickle doesn't like embedded classes
    globals()[ExampleExecutor.__name__] = ExampleExecutor

    deferred = []
    for i in range(2):
        deferred_executor = Deferred(ExampleExecutor, i)
        deferred.append(deferred_executor)

    p = Parallelize(deferred)
    try:
        print "len(p.executors) = %d" % len(p.executors)

        for executor in p.executors:
            print executor.pid

        for i in range(2):
            p(i)

        p.wait()
        print "p.results: " + `p.results`
    finally:
        p.stop()
        print "after stop"

def test3():
    def square(i):
        import time
        time.sleep(1)
        return i * i

    # pickle doesn't like embedded functions
    globals()[square.__name__] = square

    square = Parallelize([ square ] * 10)
    print "Allocated children"

    try:
        for i in range(10):
            square(i)

        print "Queued parallelized invocations. Ctrl-C to abort!"
        for i, result in enumerate(square.results):
            print result

        print "len(iresults) == " + `i + 1`

    finally:
        aborted = square.stop()
        if aborted:
            print "len(aborted) = %d" % len(aborted)
            print "len(aborted) + len(results) = %d" % (len(aborted) + len(square.results))

        print "len(pool.results) = %d" % len(square.results)

if __name__ == "__main__":
    test3()
