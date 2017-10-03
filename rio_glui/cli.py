"""rio_glui.cli"""

import logging
from io import BytesIO
from cachetools.func import lru_cache

import click
import numpy as np

from PIL import Image
from flask import Flask, render_template, jsonify, send_file, abort

import mercantile

import rasterio as rio
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.warp import transform_bounds
from rio_color.operations import parse_operations
from rio_color.utils import scale_dtype, to_math_type

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app = Flask(__name__)


class Peeker:
    def __init__(self):
        pass

    def start(self, path, nodata, bands, img_dimension=512, tile_size=256):
        self.path = path
        self.bands = bands
        self.tile_size = tile_size
        self.img_dimension = img_dimension

        with rio.open(path) as src:
            self.wgs_bounds = list(transform_bounds(
                *[src.crs, 'epsg:4326'] +
                list(src.bounds), densify_pts=0))
            self.nodata = nodata if nodata else src.nodata
            self.count = src.count

    def tile_exists(self, z, x, y):
        mintile = mercantile.tile(self.wgs_bounds[0], self.wgs_bounds[3], z)
        maxtile = mercantile.tile(self.wgs_bounds[2], self.wgs_bounds[1], z)
        return (x <= maxtile.x + 1) and (x >= mintile.x) and (y <= maxtile.y + 1) and (y >= mintile.y)

    def get_bounds(self):
        return list(self.wgs_bounds)

    def get_ctr_lng(self):
        return (self.wgs_bounds[2] - self.wgs_bounds[0]) / 2 + self.wgs_bounds[0]

    def get_ctr_lat(self):
        return (self.wgs_bounds[3] - self.wgs_bounds[1]) / 2 + self.wgs_bounds[1]

    @lru_cache()
    def get_tile(self, z, x, y):
        tile = mercantile.Tile(x=x, y=y, z=z)
        w, s, e, n = mercantile.xy_bounds(tile)

        with rio.open(self.path) as src:
            with WarpedVRT(src,
                           dst_crs='EPSG:3857',
                           threads=4,
                           resampling=Resampling.bilinear,
                           src_nodata=self.nodata,
                           dst_nodata=self.nodata) as vrt:
                                window = vrt.window(w, s, e, n, precision=21)
                                out = vrt.read(window=window,
                                               boundless=True,
                                               resampling=Resampling.bilinear,
                                               out_shape=(self.count, self.img_dimension, self.img_dimension),
                                               indexes=self.bands).astype(np.uint8)

        mask_shape = (1,) + out.shape[-2:]
        mask = np.full(mask_shape, 255, dtype=np.uint8)
        if self.nodata is not None:
            mask[0] = np.all(np.dstack(out) != self.nodata, axis=2).astype(np.uint8) * 255

        out = np.concatenate((out, mask))

        return out


def apply_color(imgarr, color):
    try:
        for ops in parse_operations(color):
            imgarr = scale_dtype(ops(to_math_type(imgarr)), np.uint8)
    except ValueError as e:
        raise click.UsageError(str(e))

    return Image.fromarray(np.dstack(imgarr))


pk = Peeker()


@app.route('/')
def main_page():
    return render_template(
        'preview.html',
        ctrlat=pk.get_ctr_lat(),
        ctrlng=pk.get_ctr_lng(),
        tile_size=pk.tile_size,
        bounds=pk.wgs_bounds)


@app.route('/tiles/<rdate>/<color>/<z>/<x>/<y>.png')
def get_image(color, rdate, z, x, y):
    z, x, y = [int(t) for t in [z, x, y]]
    if not pk.tile_exists(z, x, y):
        abort(404)

    tilearr = pk.get_tile(z, x, y)
    img = apply_color(tilearr, color)

    sio = BytesIO()
    img.save(sio, 'PNG')
    sio.seek(0)

    return send_file(sio, mimetype='image/png')


@app.route('/getbounds', methods=['GET', 'POST'])
def set_source():
    return jsonify(pk.get_bounds())


@click.command()
@click.argument('srcpath', type=click.Path(exists=True))
@click.option('--nodata', '-n', type=int)
@click.option('--bidx', '-b', type=str, default='1,2,3')
@click.option('--shape', type=int, default=512)
@click.option('--tile-size', type=int, default=512)
@click.option('--prt', type=int, default=5000,
              help="the port of the webserver. Defaults to 5000.")
def glui(srcpath, nodata, bidx, shape, tile_size, prt):

    bands = [int(b) for b in bidx.split(',')]
    if len(bands) != 3:
        click.Exception('invalid bdix format')

    click.echo('Inspecting {0} at http://127.0.0.1:{1}/'.format(srcpath, prt), err=True)

    pk.start(srcpath, nodata, bands, shape, tile_size)
    click.launch('http://127.0.0.1:{}/'.format(prt))
    app.run(threaded=True, port=prt)
