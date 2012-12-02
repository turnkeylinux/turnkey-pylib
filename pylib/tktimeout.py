from Tkinter import *
import threading
import time

class Timeout:
    """class providing timeout dialog, designed to be inherited

       methods to override:
           _dialog()  : called with *args passed to __init__
                        this method should create the required dialog box

           _timeout() : called when the timeout is reached

           _periodic_actions() : called every periodic call

       usage example:
           timeout = 5
           title = 'test title'
           text = 'this is test text for the dialog'
           Timeout(timeout, title, text).wait_selection()
    """

    def __init__(self, timeout, title, *args):
        """returns selection"""
        self.root = Tk()
        self.root.title(title)

        self.countdown = StringVar()

        self.timeout = timeout
        self.time_lapsed = 0

        self.selected = None
        self.running = True

        self.thread1 = threading.Thread(target=self._worker_thread)
        self.thread1.start()

        self._dialog(*args)

    def _dialog(self, text="timeout testing dialog"):
        """creates example dialog for testing"""
        frame1 = Frame(self.root)
        l = Label(frame1, text=text)
        l.grid(row=0, columnspan=1, stick=W)

        Label(frame1, textvariable=self.countdown).grid(row=2,
                                                        column=0,
                                                        stick=N+S+E+W)

        frame1.grid(row=0, stick=N+E+S+W)

    def _timeout(self):
        """do this when timeout is reached"""
        self.running = False

    def _periodic_actions(self):
        pass

    def _periodic_call(self):
        """check every X ms if there is something new in the queue"""
        ms = 100
        if not self.running:
            self.root.destroy()
            return "break"

        self.time_lapsed += ms
        self._periodic_actions()

        if self.time_lapsed == (self.timeout * 1000):
            self._timeout()

        self.after_id = self.root.after(ms, self._periodic_call)

    def _worker_thread(self):
        """this is where we handle the asynchronous I/O"""
        countdown = self.timeout
        while self.running:
            self.countdown.set(countdown)
            time.sleep(1)
            countdown -= 1

    def wait_selection(self):
        self._periodic_call()
        self.root.mainloop()

        self.running = False
        self.root.after_cancel(self.after_id)

        return self.selected

def test():
    timeout = 5
    title = 'test title'
    text = 'this is test text for the dialog'
    Timeout(timeout, title, text).wait_selection()

if __name__ == "__main__":
    test()

