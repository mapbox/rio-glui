from flask import Flask, render_template, request, jsonify, url_for, send_file, abort

import click
import shutil, tempfile, os

import rasterio as rio
import numpy as np

from rio_color.operations import parse_operations, gamma, sigmoidal, saturation
from rio_color.utils import scale_dtype, to_math_type

from functools import lru_cache

from io import StringIO, BytesIO
from rasterio import transform, windows
from rasterio.warp import reproject, Resampling, transform_bounds


import boto3
import re

from io import BytesIO
import numpy as np
from PIL import Image


client = boto3.client('s3')

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

import mercantile
from PIL import Image


app = Flask(__name__)


def adjust_key(key):
    typepattern = "scenes\/(?P<z>[0-9]+)-(?P<x>[0-9]+)-(?P<y>[0-9]+)-(?P<source_id>[a-z0-9_]+)-(?P<date>(19|20)[0-9]{2}([0-9]{4})?)-(?P<scene_id>[a-z0-9_]+)\.(?P<ext>(txt|tif))$"
    match = re.match(typepattern, key, re.IGNORECASE)

    if match:
        return 'previews/{source_id}/{date}/{scene_id}/{z}-{x}-{y}-{source_id}-{date}-{scene_id}.png'.format(**match.groupdict())

def load_img(key):
    response = client.get_object(
        Bucket='mapbox-pxm',
        Key=key)

    with BytesIO(response['Body'].read()) as src:
        data_arr = np.array(Image.open(src))
        return data_arr

def load_zxys(z, x, y, source):
    prefix = 'scenes/{z}-{x}-{y}-{source}'.format(z=z, x=x, y=y, source=source)
    img = np.zeros((1024, 1024, 4), dtype=np.uint8)
    response = client.list_objects_v2(
            Bucket='mapbox-pxm',
            Prefix=prefix)

    if 'Contents' in response:
        for k in response['Contents']:
            pkey = adjust_key(k['Key'])
            if pkey is not None:
                timg = load_img(pkey)
                mask = timg[:, :, -1] == 255
                img[mask] = timg[mask]
                
        return np.rollaxis(img, 2, 0)


class ScenePeeker:
    def __init__(self):
        pass

    def start(self, source, tile_size=256, center=[-122.0, 38.0]):
        self.source = source
        self.tile_size = tile_size
        
        self.lat = center[1]
        self.lng = center[0]

    @lru_cache()
    def get_tile(self, z, x, y):
        return load_zxys(z, x, y, self.source)


def apply_color(imgarr, color):
    try:
        for ops in parse_operations(color):
            imgarr = scale_dtype(ops(to_math_type(imgarr)), np.uint8)
    except ValueError as e:
        raise click.UsageError(str(e))

    return Image.fromarray(np.dstack(imgarr))


pk = ScenePeeker()


@app.route('/')
def main_page():
    return render_template('preview.html', ctrlat=pk.lat, ctrlng=pk.lng, tile_size=pk.tile_size)


@app.route('/tiles/<rdate>/<color>/<z>/<x>/<y>.png')
def get_image(color, rdate, z, x, y):
    z, x, y = [int(t) for t in [z, x, y]]

    
    tilearr = pk.get_tile(z, x, y)

    if tilearr is None:
        abort(404)

    img = apply_color(tilearr, color)

    sio = BytesIO()
    img.save(sio, 'PNG')
    sio.seek(0)

    return send_file(sio, mimetype='image/png')


@click.command()
@click.argument('source', type=str)
@click.option('--tile-size', type=int, default=512)
@click.option('--center', type=str, default='[-122.0, 38.0]')
@click.option('--prt', type=int, default=5000,
            help= "the port of the webserver. Defaults to 5000.")
def glui(source, tile_size, center, prt):
    center = eval(center)

    pk.start(source, tile_size, center)
    click.echo('Inspecting {0} at http://127.0.0.1:{1}/'.format(source, prt), err=True)
    app.run(threaded=True, port=prt)
