========
rio-glui
========

.. image:: https://circleci.com/gh/mapbox/rio-glui.svg?style=svg
   :target: https://circleci.com/gh/mapbox/rio-glui

.. image:: https://codecov.io/gh/mapbox/rio-glui/branch/master/graph/badge.svg
 :target: https://codecov.io/gh/mapbox/rio-glui

Explore CloudOptimized geotiff on your browser using Mapbox GL JS.

.. image:: http://i.giphy.com/3ohzdVQrl8uUc8I2dO.gif

Install
=======

You can install rio-glui using pip

.. code-block:: console

  $ pip install -U pip
  $ pip install rio-glui


or install from source:

.. code-block:: console

  $ git clone https://github.com/mapbox/rio-glui.git
  $ cd rio-glui
  $ pip install -e .

Usage
=====

.. code-block:: console

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

Explore COG hosted on aws

.. code-block:: console

  $ rio glui https://oin-hotosm.s3.amazonaws.com/5ac626e091b5310010e0d482/0/5ac626e091b5310010e0d483.tif


**Playground**

The **--playground** option opens a *playground* template where you an interact with the data to apply *rio-color formula*.


Creating CloudOptimized Geotiff
===============================

To create rio-glui friendly files (CloudOptimized Geotiff) you can use another rasterio plugin: rio-cogeo (https://github.com/mapbox/rio-cogeo.git).


Extras
======

This plugin also enable raster visualisation in Jupyter Notebook using [`mapboxgl-jupyter`](https://github.com/mapbox/mapboxgl-jupyter)


Contribution & Devellopement
============================

Issues and pull requests are more than welcome.

**Dev install & Pull-Request**

.. code-block:: console

  $ git clone https://github.com/mapbox/rio-glui.git
  $ cd rio-cogeo
  $ pip install -e .[dev]

*Python3.6 only*

This repo is set to use `pre-commit` to run *flake8*, *pydocstring* and *black* ("uncompromising Python code formatter") when commiting new code.

.. code-block:: console

  $ pre-commit install
  $ git add .
  $ git commit -m'my change'
  black....................................................................Passed
  Flake8...................................................................Passed
  Verifying PEP257 Compliance..............................................Passed
  $ git push origin
