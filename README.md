# layouteditor

A wrapper for pylayout, the Python module for Juspertor LayoutEditor.

It includes
 
- `wrapper.py`, which contains wrapper classes for the pylayout objects

- `interactive.py`, which is a template script that starts LayoutEditor and can be extended to draw layouts.

- `components.py`, which contains a few example functions that create components that are useful to our work.


## Imports

The compiled object `pylayout.so` relies on being able to import the specific bundled versions of SIP and PyQt4, and `pylayout.so` will fail to load if the Python import machinery finds other versions first. The developer recommends using `pylayout` by running code directly from its directory.

To make the imports in `wrapper.py` function correctly, install the current `pylayout` directory in a location on the Python path as `pylayout` (this can be done with a softlink, if you have multiple installations) and create in it a blank `__init__.py` file to make it a valid package. Once this is done, the command `$ ipython -i interface.py` should start LayoutEditor and an IPython session that has a Layout and a Drawing object in scope. Designs can be drawn completely in a script, or can be finished by hand using the GUI.
