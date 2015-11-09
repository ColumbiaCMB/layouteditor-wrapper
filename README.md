# layouteditor

layouteditor is a Python interface for Juspertor LayoutEditor.

It includes the following:
 
- an new interface (interface.py) to the pylayout Python bindings that enables more 
flexibility, such as the use of user units instead of database units;
 
- a template script (interactive.py) that starts LayoutEditor with an embedded IPython session, 
which allows the user to run Python code from the terminal while also using the graphical interface; 

- a small library of functions that create components that are useful to our work. 


## Imports

The compiled object `pylayout.so` relies on specific versions of SIP and PyQt4, which are provided with the package. 
On a system with newer versions of SIP or PyQt4, `pylayout.so` will fail to load if it find the other versions first.
The recommended way to install pylayout is to run code directly from the package directory.

However, the interactive script is most useful when copied to a project directory and modified specifically for that 
project. Making the imports work from outside the pylayout directory requires some modifications. To make the script 
imports function correctly, install the current `pylayout_YYYYMMDD` directory in a location on the Python path as 
`pylayout_current` (this can be done with a softlink) and create in it a blank `__init__.py` file.

Modifications specific to various operating systems are below.

### Linux

Fill me in!

### Windows

Fill me in!

### OS X

The bundled versions of PyQt4 and sip expect these libraries to be available in `/Library/Python/2.7/site-packages`, 
which is the default site-packages directory on OS X. The `PyQt4` directory and the `sip.so` file can be moved to 
this location, or one can create softlinks back to the bundled versions.

