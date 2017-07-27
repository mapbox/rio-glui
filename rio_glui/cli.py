from functools import lru_cache
from io import BytesIO
import logging

from PIL import Image
from flask import Flask, render_template, jsonify, send_file, abort
from rasterio import transform
from rasterio.crs import CRS
from rasterio.warp import reproject, Resampling, transform_bounds
from rio_color.operations import parse_operations
from rio_color.utils import scale_dtype, to_math_type
import click
import mercantile
import numpy as np
import rasterio as rio

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)


class Peeker:
    def __init__(self):
        pass

    def start(self, path, img_dimension=512, tile_size=256):
        self.path = path
        self.tile_size = tile_size
        self.img_dimension = img_dimension
        with rio.open(path) as src:
            self.wgs_bounds = transform_bounds(
                *[src.crs, 'epsg:4326'] +
                list(src.bounds), densify_pts=0)

    def tile_exists(self, z, x, y):
        mintile = mercantile.tile(self.wgs_bounds[0], self.wgs_bounds[3], z)
        maxtile = mercantile.tile(self.wgs_bounds[2], self.wgs_bounds[1], z)
        return (x <= maxtile.x + 1) and (x >= mintile.x) and \
               (y <= maxtile.y + 1) and (y >= mintile.y)

    def get_bounds(self):
        return list(self.wgs_bounds)

    def get_ctr_lng(self):
        return (self.wgs_bounds[2] - self.wgs_bounds[0]) / 2 + self.wgs_bounds[0]

    def get_ctr_lat(self):
        return (self.wgs_bounds[3] - self.wgs_bounds[1]) / 2 + self.wgs_bounds[1]

    # @lru_cache()
    def get_tile(self, z, x, y):
        bounds = [c for i in (mercantile.xy(*mercantile.ul(x, y + 1, z)), mercantile.xy(*mercantile.ul(x + 1, y, z))) for c in i]
        toaffine = transform.from_bounds(*bounds + [self.img_dimension, self.img_dimension])

        with rio.open(self.path) as src:
            source_arr = src.read()
            count = src.count
            nodatavals = src.nodatavals
            source_transform = src.transform
            source_crs = src.crs

        dest_arr = np.zeros(
            (src.count, self.img_dimension, self.img_dimension), dtype=np.uint8)

        reproject(
            source_arr, dest_arr,
            src_transform=source_transform,
            dst_transform=toaffine,
            src_crs=source_crs,
            dst_crs=CRS({'init': 'epsg:3857'}),
            resampling=Resampling.bilinear)

        if count == 3:
            alpha = np.empty((1, self.img_dimension, self.img_dimension), dtype=np.uint8)
            out = np.concatenate(dest_arr, alpha)
            if nodatavals:
                out[-1] = np.all(dest_arr != nodatavals,
                                 axis=2).astype(np.uint8) * 255
            else:
                out[-1] = 255
        else:
            out = dest_arr

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
        'preview.html', ctrlat=pk.get_ctr_lat(), ctrlng=pk.get_ctr_lng(),
        tile_size=pk.tile_size)


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
@click.option('--shape', type=int, default=512)
@click.option('--tile-size', type=int, default=512)
@click.option('--prt', type=int, default=5000,
              help="the port of the webserver. Defaults to 5000.")
def glui(srcpath, shape, tile_size, prt):
    pk.start(srcpath, shape, tile_size)
    click.echo('Inspecting {0} at http://127.0.0.1:{1}/'.format(srcpath, prt), err=True)
    click.launch('http://127.0.0.1:{}/'.format(prt))
    app.run(threaded=True, port=prt)
