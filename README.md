# RCam - Remote Controllable Camera Recordings from industrial high-speed cameras

A Qt-desktop app for recording from Imaging Source Cameras that can be controlled remotely
via a REST interface and can receive events. Based on the [PySide6
demoapp](https://github.com/TheImagingSource/ic4-examples), licensed with the APACHE
license.

[![Python Tests](https://github.com/brain-bremen/rcam/actions/workflows/python-tests.yml/badge.svg)](https://github.com/brain-bremen/rcam/actions/workflows/python-tests.yml)

![Screenshot](images/screenshot.png)


## Execute the GUI with uv

```
uvx --from git+https://github.com/brain-bremen/rcam rcam
```

## Test REST API

While the GUI is running, go to http://localhost:8000/docs to explore the REST API.


## Distribute via pyinstaller (for Windows only)

```
# create new spec file
pyinstaller .\src\rcam\gui.py  --collect-binaries imagingcontrol4 --add-data ".\images;images" --name "rcam" --contents-directory "." --window --icon .\images\tis.ico
# or use existing
pyinstaller rcam.spec
```
