# layouteditor
This repository is an interface for Juspertor LayoutEditor and inclues associated design tools.

## Imports

The imports in pylayout are a little messy. The compiled object `pylayout.so` relies on old versions of SIP and PyQt4, which are provided with the package. The recommended way to install pylayout is to run code directly from the package directory. On a system with newer versions of SIP or PyQt4, `pylayout.so` will fail to load because it will find the other versions first.

As a temporary fix, I recommend adding three softlinks to the pylayout versions of `pylayout.so`, `sip.so`, and `PyQt4`. These are listed in .gitignore so they won't be added to this repository.  I'm working on a cleaner way to fix this. 
