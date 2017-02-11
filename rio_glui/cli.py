from flask import Flask, render_template, request, jsonify, url_for, send_file, abort

import click
import shutil, tempfile, os

import rasterio as rio
import numpy as np

from rio_color.operations import parse_operations, gamma, sigmoidal, saturation
from rio_color.utils import scale_dtype, to_math_type

from io import StringIO, BytesIO
from rasterio import transform
from rasterio.warp import reproject, RESAMPLING, transform_bounds

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

    def get_tile(self, z, x, y):
        bounds = [c for i in (mercantile.xy(*mercantile.ul(x, y + 1, z)), mercantile.xy(*mercantile.ul(x + 1, y, z))) for c in i]
        toaffine = transform.from_bounds(*bounds + [512, 512])

        out = np.empty((4, 512, 512), dtype=np.uint8)

        for i in range(self.src.count):
            reproject(
                rio.band(self.src, i + 1), out[i],
                dst_transform=toaffine,
                dst_crs="init='epsg:3857'",
                resampling=RESAMPLING.bilinear)

        if self.src.count == 3:
            if self.src.nodatavals:
                out[-1] = np.all(np.dstack(out[:3]) != self.src.nodatavals, axis=2).astype(np.uint8) * 255
            else:
                out[-1] = 255

        return out

def recursepath(basepath, path_components):
    path_components = [str(p) for p in path_components]
    tpath = os.path.join(*[basepath] + path_components)
    if not os.path.exists(tpath):
        for i, p in enumerate(path_components):
            tpath = os.path.join(*[basepath] + path_components[:i+1])
            if not os.path.exists(tpath):
                os.mkdir(tpath)
                
    return tpath

class IMGCacher:
    def __init__(self):
        self.tmpdir = tempfile.mkdtemp()

    def add(self, img, z, x, y):
        directory = recursepath(self.tmpdir, [z, x])
        cachetile = os.path.join('{0}/{1}.png'.format(directory, y))

        log.debug('Caching tile at {0}'.format(cachetile))
        img.save(cachetile)

    def load(self, z, x, y):
        cachetile = os.path.join('{0}/{1}/{2}/{3}.png'.format(self.tmpdir, z, x, y))
        if os.path.exists(cachetile):
            log.debug('Loading cached tile at {0}'.format(cachetile))
            with rio.open(cachetile) as src:
                return src.read()
        else:
            return None

        
    def __enter__(self):
        return self
    def __exit__(self, ext_t, ext_v, trace):
        shutil.rmtree(self.tmpdir)
        if ext_t:
            click.echo("in __exit__")

pk = Peeker()
fc = IMGCacher()

@app.route('/')
def main_page():
    return render_template('preview.html', ctrlat=pk.get_ctr_lat(), ctrlng=pk.get_ctr_lng())


@app.route('/tiles/<color>/<z>/<x>/<y>.png')
def get_image(color, z, x, y):

    z, x, y = [int(t) for t in [z, x, y]]
    if not pk.tile_exists(z, x, y):
        abort(404)

    # try to load from cache
    tilearr = fc.load(z, x, y)

    if tilearr is None:
        tilearr = pk.get_tile(z, x, y)

    try:
        for ops in parse_operations(color):
            color_tilearr = scale_dtype(ops(to_math_type(tilearr)), np.uint8)
    except ValueError as e:
        raise click.UsageError(str(e))

    img = Image.fromarray(np.dstack(color_tilearr))
    # put in cache
    fc.add(img, z, x, y)

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
    app.run(debug=True, port=12345)
