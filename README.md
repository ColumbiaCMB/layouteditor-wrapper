# layouteditor-wrapper

A wrapper for pylayout, the Python module for Juspertor LayoutEditor. This package is not developed or endorsed in any way by Juspertor.

## Contents

The package will be installed as `layouteditorwrapper`. It includes
 
- `wrapper.py`, which contains wrapper classes for the pylayout objects.

- `path.py`, which contains classes and functions useful for drawing co-planar waveguide components. 

- `components.py`, which contains a few example functions that create useful components.

There is also a template script `interactive.py` that starts LayoutEditor with `wrapper.Layout` and `wrapper.Drawing` objects in the namespace:

`$ ipython -i interactive.py`

This script can be used as a template to create layouts partly or entirely in code. If the wrapper objects are available in a terminal session, one can draw with the GUI and in code at the same time.

## Installation

The only dependency is numpy.

The compiled object `pylayout.so` relies on being able to import specific versions of SIP and PyQt4, and it will fail to load if the Python import machinery finds other versions first. These specific versions may be quite old, so this restriction could make it difficult to install more current software. To get around this issue, `wrapper.py` imports `pylayout` and inserts its path first into `sys.path`, makes the imports necessary to start LayoutEditor, then removes this entry from the path. For this to work, the `pylayout.so` object must be available on `sys.path`, and the correct versions of SIP and PyQt4 must be either in the same directory or the first ones encountered on the path.
  
### Linux

Pylayout is not included in the generic Linux download, but it included only with the versions that correspond to specific distributions. In these specific versions, pylayout is built against the SIP and PyQt4 versions that are included with the system Python.

### macOS

The macOS versions of pylayout are bundled with the correct versions of PyQt4 and SIP. Simply add the distributed `pylayout` directory to `sys.path` -- for example, by including it in the `PYTHONPATH` environment variable. Since the required versions will also be in this directory, this package should work in any environment. 

### Windows

Windows installation has not been tested with this code.

## Troubleshooting

If the LayoutEditor window freezes or fails to pop up a window, try hitting enter in the interactive terminal window. If the interactive session is IPython, try hitting `ctrl-d` to bring up the Quit IPython prompt. On macOS, these steps should un-freeze LayoutEditor.
