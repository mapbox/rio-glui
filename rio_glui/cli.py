from flask import Flask, render_template, request, jsonify, url_for, send_file, abort

import click
import shutil, tempfile, os

import rasterio as rio
import numpy as np

from rio_color.operations import parse_operations, gamma, sigmoidal, saturation
from rio_color.utils import scale_dtype, to_math_type

from functools import lru_cache


from io import StringIO, BytesIO
from rasterio import transform
from rasterio.warp import reproject, Resampling, transform_bounds

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

import mercantile
from PIL import Image

app = Flask(__name__)

class Peeker:
    def __init__(self):
        pass

    def start(self, path):
        self.src = rio.open(path)
        self.wgs_bounds = transform_bounds(*[self.src.crs, 'epsg:4326'] + list(self.src.bounds), densify_pts=0)

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
        bounds = [c for i in (mercantile.xy(*mercantile.ul(x, y + 1, z)), mercantile.xy(*mercantile.ul(x + 1, y, z))) for c in i]
        toaffine = transform.from_bounds(*bounds + [512, 512])

        out = np.empty((4, 512, 512), dtype=np.uint8)

        for i in range(self.src.count):
            reproject(
                rio.band(self.src, i + 1), out[i],
                dst_transform=toaffine,
                dst_crs="init='epsg:3857'",
                resampling=Resampling.bilinear)

        if self.src.count == 3:
            if self.src.nodatavals:
                out[-1] = np.all(np.dstack(out[:3]) != self.src.nodatavals, axis=2).astype(np.uint8) * 255
            else:
                out[-1] = 255

        return out


def apply_color(imgarr, color):
    print(color)
    try:
        for ops in parse_operations(color):
            color_tilearr = scale_dtype(ops(to_math_type(imgarr)), np.uint8)
    except ValueError as e:
        raise click.UsageError(str(e))

    return Image.fromarray(np.dstack(color_tilearr))


pk = Peeker()


@app.route('/')
def main_page():
    return render_template('preview.html', ctrlat=pk.get_ctr_lat(), ctrlng=pk.get_ctr_lng())


@app.route('/tiles/<color>/<z>/<x>/<y>.png')
def get_image(color, z, x, y):

    z, x, y = [int(t) for t in [z, x, y]]
    if not pk.tile_exists(z, x, y):
        abort(404)


    tilearr = pk.get_tile(z, x, y)

    img = apply_color(tilearr, color)

    ## Add color formula here!


    sio = BytesIO()
    img.save(sio, 'PNG')
    sio.seek(0)

    return send_file(sio, mimetype='image/png')

@app.route('/getbounds', methods=['GET', 'POST'])
def set_source():

    return jsonify(pk.get_bounds())

@click.command()
@click.argument('srcpath', type=click.Path(exists=True))
def glui(srcpath):
    pk.start(srcpath)
    click.echo('Inspecting {0} at http://127.0.0.1:5000/'.format(srcpath), err=True)
    app.run()
