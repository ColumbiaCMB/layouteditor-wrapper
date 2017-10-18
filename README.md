# layouteditor-wrapper

A wrapper for pylayout, the Python module for Juspertor LayoutEditor. It is not endorsed in any way by Juspertor.

The package will be installed as `layouteditorwrapper`. It includes
 
- `wrapper.py`, which contains wrapper classes for the pylayout objects.

- `path.py`, which contains classes and functions useful for drawing co-planar waveguide components. 

- `components.py`, which contains a few example functions that create useful components.

There is also a template script `interactive.py` that starts LayoutEditor:
`$ ipython -i interactive.py`
This script can be used as a template to create layouts entirely in code.

## Imports

The compiled object `pylayout.so` relies on being able to import the specific bundled versions of SIP and PyQt4, and `pylayout.so` will fail to load if the Python import machinery finds other versions first. The developer recommends using `pylayout` by running code directly from its directory.

To make the imports in `wrapper.py` function correctly, install the current `pylayout` directory in a location on the Python path as `pylayout` (this can be done with a softlink, if you have multiple installations) and create in it a blank `__init__.py` file to make it a valid package. Once this is done, the command `$ ipython -i interface.py` should start LayoutEditor and an IPython session that has a Layout and a Drawing object in scope. Designs can be drawn completely in a script, or can be finished by hand using the GUI.
