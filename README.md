# rio-glui

[![image](https://badge.fury.io/py/rio-glui.svg)](https://badge.fury.io/py/rio-glui)

[![image](https://api.travis-ci.org/mapbox/rio-glui.png)](https://travis-ci.org/mapbox/rio-glui)

[![image](https://codecov.io/gh/mapbox/rio-glui/branch/master/graph/badge.svg)](https://codecov.io/gh/mapbox/rio-glui)

Explore and adjust Cloud-optimized geotiffs
([COGs](https://www.cogeo.org/)) in your browser using
[rasterio](https://rasterio.readthedocs.io/en/stable/) and [Mapbox
GL JS](https://docs.mapbox.com/mapbox-gl-js/guides/).

<img width="700px" src="preview.png"/>

## Install

You can install rio-glui using pip

```sh
pip install -U pip
pip install rio-glui
```

or install from source:

```sh
git clone https://github.com/mapbox/rio-glui.git
cd rio-glui
pip install -e .
```

## Usage

``` console
Usage: rio glui [OPTIONS] PATH

  Rasterio glui cli.

Options:
-b, --bidx BIDX                   Raster band index
--scale INTEGER Min Max           Min and Max data bounds to rescale data from.
--colormap [cfastie|schwarzwald]  Rio-tiler compatible colormap name ('cfastie' or 'schwarzwald')
--tiles-format [png|jpg|webp]     Tile image format (default: png)
--tiles-dimensions INTEGER        Dimension of images being served (default: 512)
--nodata INTEGER                  Force mask creation from a given nodata value
--gl-tile-size INTEGER            mapbox-gl tileSize (default is the same as `tiles-dimensions`)
--port INTEGER                    Webserver port (default: 8080)
--playground                      Launch playground app
--mapbox-token TOKEN              Pass Mapbox token
--help                            Show this message and exit.
```

Example: explore COG hosted on aws

```sh
rio glui https://oin-hotosm.s3.amazonaws.com/5ac626e091b5310010e0d482/0/5ac626e091b5310010e0d483.tif
```

**Playground**

The **--playground** option opens a *playground* template where you an
interact with the data to apply *rio-color formula*.

## Creating Cloud-Optimized Geotiffs

To create rio-glui friendly files (Cloud-Optimized Geotiff) you can use
another rasterio plugin: [rio-cogeo](https://github.com/cogeotiff/rio-cogeo.git). Alternately, you can [use GDAL tools](https://gdal.org/drivers/raster/cog.html):

```sh
gdal_translate input.tif output.tif -of COG -co TILING_SCHEME=GoogleMapsCompatible -co COMPRESS=JPEG
```

## Extras

This plugin also enables raster visualisation in a Jupyter Notebook using [mapboxgl-jupyter](https://github.com/mapbox/mapboxgl-jupyter)

## Contribution & Development

Issues and pull requests are more than welcome.

**Dev install & Pull-Request**

```sh
git clone https://github.com/mapbox/rio-glui.git
cd rio-glui
pip install -e .[dev]
```

*Python3.6 only*

This repo is set to use <span class="title-ref">pre-commit</span> to run
*flake8*, *pydocstring* and *black* ("uncompromising Python code
formatter") when commiting new code.

``` console
$ pre-commit install
$ git add .
$ git commit -m'my change'
black....................................................................Passed
Flake8...................................................................Passed
Verifying PEP257 Compliance..............................................Passed
$ git push origin
```