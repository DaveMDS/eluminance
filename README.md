Eluminance
==========

A fast photo browser written in python.

![Screenshot1](https://github.com/davemds/eluminance/blob/master/data/screenshots/eluminance01.jpg)
![Screenshot2](https://github.com/davemds/eluminance/blob/master/data/screenshots/eluminance02.jpg)
![Screenshot3](https://github.com/davemds/eluminance/blob/master/data/screenshots/eluminance03.jpg)

## Usage tips ##
* The ui provide 3 hotspots to show controls on mouse hover:
  * top of the window to show the control buttons 
  * right to show the thumbnails in the current directory
  * left to show the directory tree
* Right mouse button on the photo to toggle the visibility of the tree and the thumbnails
* Mouse wheel to change zoom
* Drag the image to pan the photo

## Requirements ##

* Python 2.7 or higher
* Python-EFL 1.14 or higher
* python modules: efl, xdg

## Installation ##

* For system-wide installation (needs administrator privileges):

 `(sudo) python setup.py install`

* For user installation:

 `python setup.py install --user`

* To install for different version of python:

 `pythonX setup.py install`

* Install with a custom prefix:

 `python setup.py install --prefix=/MY_PREFIX`

* To create distribution packages:

 `python setup.py sdist`

## License ##

GNU General Public License v3 - see COPYING
