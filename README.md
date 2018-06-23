# rio-glui

Explore CloudOptimized geotiff on your browser using Mapbox GL JS.

![](http://i.giphy.com/3ohzdVQrl8uUc8I2dO.gif)

## Installation

You can install rio-glui using pip

```
  $ pip install -U pip
  $ pip install rio-guil
```

or install from source:

```
$ git clone https://github.com/mapbox/rio-glui.git
$ cd rio-glui
$ pip install -e .
```

## Usage
```
Usage: rio glui [OPTIONS] PATH

  Rasterio glui cli.

Options:
  -b, --bidx BIDX                Raster band index (default: 1,2,3)
  --tiles-format [png|jpg|webp]  Tile image format (default: png)
  --tiles-dimensions INTEGER     Dimension of images being served (default:
                                 512)
  --nodata INTEGER               Force mask creation from a given nodata value
  --gl-tile-size INTEGER         mapbox-gl tileSize (default: 512)
  --port INTEGER                 Webserver port (default: 8080)
  --playground                   Launch playground app
  --mapbox-token TOKEN           Pass Mapbox token
  --help                         Show this message and exit.
```

Explore COG hosted on aws
```
 » rio glui https://oin-hotosm.s3.amazonaws.com/5ac626e091b5310010e0d482/0/5ac626e091b5310010e0d483.tif
Inspecting https://oin-hotosm.s3.amazonaws.com/5ac626e091b5310010e0d482/0/5ac626e091b5310010e0d483.tif at http://127.0.0.1:8080/index.html
```

### Playground

The `--playground` option opens a `playgroud` template where you an interact with the data to apply `rio-color formula`


#### Creating CloudOptimized Geotiff

To create rio-glui friendly files (CloudOptimized Geotiff) you can use another rasterio plugin: [`rio-cogeo`](https://github.com/mapbox/rio-cogeo.git)


#### Extras

This plugin also enable raster visualisation in Jupyter Notebook using [`mapboxgl-jupyter`](https://github.com/mapbox/mapboxgl-jupyter)
