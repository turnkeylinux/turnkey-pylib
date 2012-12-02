<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet ekr_test?>
<leo_file>
<leo_header file_format="2" tnodes="0" max_tnode_index="48" clone_windows="0"/>
<globals body_outline_ratio="0.264737406217">
	<global_window_position top="0" left="617" height="933" width="651"/>
	<global_log_window_position top="0" left="0" height="0" width="0"/>
</globals>
<preferences/>
<find_panel_settings/>
<vnodes>
<v t="zaril.20071001195902" a="E"><vh>Project</vh>
<v t="zaril.20071001200718" a="E"><vh>development log</vh>
<v t="zaril.20071001200718.2"><vh>research</vh></v>
<v t="zaril.20071001195902.1" a="E"><vh>design</vh></v>
<v t="zaril.20071125061538" a="E"><vh>implementation</vh>
<v t="zaril.20071125061849"><vh>add modules</vh>
<v t="zaril.20071125065736"><vh>paths.py</vh></v>
<v t="zaril.20071125064338"><vh>stdtrap.py</vh></v>
<v t="zaril.20071125064413"><vh>git.py</vh></v>
</v>
<v t="zaril.20071225021219"><vh>bug: stdtrap chokes on large outputs</vh>
<v t="zaril.20071225091309"><vh>bug: empty output still deadlocks sometimes</vh></v>
</v>
<v t="zaril.20071224233211"><vh>port pyproject wrapper.py</vh></v>
<v t="zaril.20080113072415" a="TV"><vh>bug: stdtrap triggers uncaught exceptions</vh></v>
</v>
</v>
<v t="zaril.20071001200109.1"><vh>bugs/wishlist</vh></v>
</v>
</vnodes>
<tnodes>
<t tx="zaril.20071001195902">@nocolor
</t>
<t tx="zaril.20071001195902.1">goals
    object compiled
    accessible from python</t>
<t tx="zaril.20071001200109.1"></t>
<t tx="zaril.20071001200718">research distutils? (maybe it already supports this)
</t>
<t tx="zaril.20071001200718.2">SUMMARY
    getting the install location
        import distutils.sysconfig     
        print distutils.sysconfig.get_python_lib()
    
Debian package

test: install paths.py

IDEAS
    use python setup.py and then delete the source files
        if a Makefile flag is present
        OR just let the rules do it

    debian/rules doesn't use setup.py
        but its still there? for development?

    ask distutils for the install path to site-packages?

    distutils installs all packages automatically?

    extract name / maintainer / author_email / description from Debian control file

    debian/
    pylib/
    setup.py
    
Q: can pyo code be used from non -O interpreter?
A:
    no, you'll only be able to access it from similarly optimized   
    but you can install from source if you want to do that
        which a developer probably would
---
Q: does distutils support object compiling?
A:
    yes -O2
---
Q: how does it know where to install the libraries?
A:
    distutils.sysconfig.get_python_lib() does that
        I think the Python configuration is embedded into Python
---


RESOURCE: file:///usr/share/doc/python-docs/html/dist/dist.html

example
    from distutils.core import setup
    setup(name='foo',
          version='1.0',
          py_modules=['foo'])


python setup.py sdist
python setup.py install
    copies build/lib/paths.py -&gt; /usr/lib/python2.4/site-packages

    
python setup.py bdist_wininst
    creates a windows install file

python setup.py bdist --help-formats

puts stuff in dist/

from pyproject Makefile
    PYCC=python -O $(PYTHON_LIB)/py_compile.py
    PYCC_NODOC=python -OO $(PYTHON_LIB)/py_compile.py

python setup.py install -O2  
    no strings in Python -O2

python setup.py install --root path/to/alternate/root

Q: how do I recognize python modules automatically?
A:
    packages = [ '' ]
    package_dir = {'': 'pylib'}
        if the name is non-empty you are promising foo/__init__.py

example minimum setup.py

    from distutils.core import setup
    setup(packages = [''],
          package_dir = {'': 'pylib'})</t>
<t tx="zaril.20071125061538">__add__

connagent modules?
    fileevent
    popen4?
</t>
<t tx="zaril.20071125061849">* TODO
merge all versions of each module
    to prevent breakage

    howto
        get original (by date)
        get latest in branch a and b
    
        merge -p branch1 orig branch2 &gt; new
    
remove all inclusions in the variuos pyprojects
create dependency to sterile-pylib
commit
    removed stdtrap.py (sterile-pylib)

* MODULES
    paths
    stdtrap
    git

    debinfo
        ar
        hashstore

</t>
<t tx="zaril.20071125064338">Sumo was the latest version
removed from sumo, covin and deckdebuild
</t>
<t tx="zaril.20071125064413">covin
pool
sumo
</t>
<t tx="zaril.20071125065736">deckdebuild
deck
pool
sumo
</t>
<t tx="zaril.20071224233211">
Q: what do we call this?
alternatives
    toolkit
    pyproject
    cli high
    commands
    wrapper
    pycli
    cli toolkit    
    pyproject_common
    pyproject shared
    skeleton

A:
    pyproject.CliWrapper

* IDEAS
    override base class
    class method only?
    integrate version.py with cli_toolkit

    does a class have an embedded file parameter?
        or module parameter from which we can access file

--debug and --profile should be supported at the level of the wrapper too

    maybe pyproject installs a library? (instead of putting pyproject_wrapper in sterile-pylib)
 
Q: what functionality does the wrapper implement?
autoversioning (pyproject specific)

</t>
<t tx="zaril.20071225021219">SUMMARY:
    it turns out the thread was also blocked
        this is probably a Python threading bug

* TEST:
def test2():
    trap = StdTrap(stdout=True, stderr=False)
    try:
        print "A" * 4094
    finally:
        trap.close()

    output = trap.stdout.read()
    print "===="
    print output

* GOTCHA: I can't debug by writing to stdout
WORKAROUND: write to a log file...

class Log:
    def __init__(self, path):
        if os.path.exists(path):
            os.remove(path)

        self.fh = file(path, "w")

    def write(self, s):
        self.fh.write(s)
        self.fh.flush()

DISCOVERY: adding a small sleep between prints makes stuff work
   
From the manual:
    Not all built-in functions that may block waiting for I/O allow other threads to run. (The most popular ones (time.sleep(), file.read(), select.select()) work as expected.)


how do I set non blocking mode?

IDEAS
    run the splicer in a separate process

splicer logic:
    select the spliced_fd_reader and the splicer_pipe writer
    when I can read from spliced_fd_reader, read into a buffer
    when I have something to write, and I can write into splicer_pipe, then write
    if spliced_fd 
    
BUG: if stderr + stdout, stdtrap jams
    hypo: the splicer_read fds are being replicated into the child
        so it never gets the hup signal

    IDEAS: 
        keep track of fds
            what if some other piece of code forks?
        signal to the child to close shop

* TODO:
refactor _splice
    don't need to save transparent in self

IDEA: don't intercept stdout/stderr for the subprocess
    freeze after exit so I can see what the process fd map is like


</t>
<t tx="zaril.20071225091309">def test4():
    s = StdTrap(transparent=True)
    s.close()
    print 'nothing in stdout: """%s"""' % s.stdout.read()
    print 'nothing in stderr: """%s"""' % s.stderr.read()

hypo: some kind of race condition

TEST:

while true; do
    python stdtrap.py # running test4
done


E: insert a 1/10 second delay between StdTrap and s.close()
R: no deadlocks

IDEA: use an opposite signalling mechanism to block until the child starts?

put the entire child splicer in a try clause?
    IOError (interrupted by system call)
</t>
<t tx="zaril.20080113072415">SUMMARY  
    the stash is being closed because of an exception
        the exception is suppressed because of stdtrap.getoutput()
            the exception is happening in the stdtrap subprocess
    
    this causes code to "jump out" of the splicer and trigger opened's finally clause

    the first exception was caused by an error closing stdout (which had already been closed)

    even if that was fixed there would still be an error because sys.exit itself triggers an exception

    how I debugged this
        log debug messages to file (Log class)
        peppered splicer with marks to trace execution
        printing traceback manually with traceback.print_exc(file=log)
        by freezing the process with sleep and examining fd map

SOLUTION: use os._exit instead of sys.exit

TEST: 
    cd stashes
    rm -rf alon; cp -a alon.bak alon; (cd alon &amp;&amp; covin-sync-local)

ISOLATED:

def test5():
    def func():
        pass

    print "output: " + getoutput(func)

DISCOVERY: exception is raised in any case

* IDEAS
try to see if StdTrap also produces bug...
    yes it does

try to see where the bug is triggered...
    litter code with Log to file entries
        when the exception is raised it should terminate

os.getpid() at the exception

Q: why is the exception only triggered once?
A: because after triggering the close sync_local doesn't reach getoutput any more

Q: could the exception really be triggered AFTER sys.exit()?
IDEA: print the pid and timestamp
    right before the exit: mark 14 (30162, 1200267545.397315)
    in the opened decorator: CLOSING: (30162, 1200267545.397519)
A: yes, somehow the sys.exit(0) was triggering an exception that jumped out AFTER
sys.exit(0)

GOTCHA: sys.exit(0) raises an exception - so its caught by a try clause elsewhere


    </t>
</tnodes>
</leo_file>
