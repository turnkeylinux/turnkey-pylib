<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet ekr_test?>
<leo_file>
<leo_header file_format="2" tnodes="0" max_tnode_index="48" clone_windows="0"/>
<globals body_outline_ratio="0.0883333333333">
	<global_window_position top="0" left="469" height="658" width="800"/>
	<global_log_window_position top="0" left="0" height="0" width="0"/>
</globals>
<preferences/>
<find_panel_settings/>
<vnodes>
<v t="zaril.20071001195902" a="E"><vh>Project</vh>
<v t="zaril.20071001200718" a="E"><vh>development log</vh>
<v t="zaril.20071001200718.2" a="ETV"><vh>research</vh></v>
<v t="zaril.20071001195902.1" a="E"><vh>design</vh></v>
<v t="zaril.20071001200718.3" a="E"><vh>implementation</vh></v>
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
<t tx="zaril.20071001200718.3"></t>
</tnodes>
</leo_file>
