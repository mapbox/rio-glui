# rio-glui

Demo rasterio / Mapbox GL JS demo app

![](http://i.giphy.com/3ohzdVQrl8uUc8I2dO.gif)

## Installation

```
» git clone git@github.com:mapbox/rio-glui.git
» cd rio-glui
» pip install -e .
```

## Usage
```
Usage: rio glui [OPTIONS] SRCPATH

Options:
  --shape INTEGER
  --tile-size INTEGER
  --prt INTEGER        the port of the webserver. Defaults to 5000
  --help               Show this message and exit.
```
eg
```
 » rio glui ~/pxm/test/expected/composite/composite_ca_chilliwack_rgba.tif
Inspecting /Users/dnomadb/pxm/test/expected/composite/composite_ca_chilliwack_rgba.tif at http://127.0.0.1:5000/
```

## Working big file
If you plan to use `rio-glui` on a large image you may want to create `overviews` before.
Creating internal overview will make your file bigger but rio-glui will be much faster.

e.g
```
rio overview --build 2,4,8,16,32,64,128,256,512 myraster.tif
rio glui myraster.tif
```
