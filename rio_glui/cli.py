from __future__ import print_function
import os

from aiohttp import web
import aiohttp_jinja2
import jinja2

import json
import click
from io import BytesIO

import numpy as np

import rasterio as rio
from rasterio import transform
from rasterio.warp import reproject, transform_bounds, Resampling

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

import mercantile
from PIL import Image

from cachetools.func import lru_cache

app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

class Peeker:
    def __init__(self):
        pass

    def start(self, path):
        self.src = rio.open(path)
        self.wgs_bounds = transform_bounds(*[self.src.crs, 'epsg:4326'] + list(self.src.bounds), densify_pts=0)

    @lru_cache()
    def tile_exists(self, z, x, y):
        mintile = mercantile.tile(self.wgs_bounds[0], self.wgs_bounds[3], z)
        maxtile = mercantile.tile(self.wgs_bounds[2], self.wgs_bounds[1], z)
        return (x <= maxtile.x + 1) and (x >= mintile.x) and (y <= maxtile.y + 1) and (y >= mintile.y)

    @lru_cache()
    def get_bounds(self):
        return list(self.wgs_bounds)

    @lru_cache()
    def get_ctr_lng(self):
        return (self.wgs_bounds[2] - self.wgs_bounds[0]) / 2 + self.wgs_bounds[0]

    @lru_cache()
    def get_ctr_lat(self):
        return (self.wgs_bounds[3] - self.wgs_bounds[1]) / 2 + self.wgs_bounds[1]

    # def __rescale_intensity__(image, in_range=[0,16000], out_range=[1,255]):
    #     imin, imax = in_range
    #     omin, omax = out_range
    #     image = np.clip(image, imin, imax) - imin
    #     image = image / float(imax - imin)
    #     return (image * (omax - omin) + omin)

    @lru_cache()
    def get_tile(self, z, x, y, tileformat='png', color=''):

        tilesize = 256

        if tileformat == 'jpg':
            tileformat = 'jpeg'
        try:
            bounds = [c for i in (mercantile.xy(*mercantile.ul(x, y + 1, z)), mercantile.xy(*mercantile.ul(x + 1, y, z))) for c in i]
            toaffine = transform.from_bounds(*bounds + [tilesize, tilesize])

            out = np.empty((4, tilesize, tilesize), dtype=np.uint8)

            reproject(
                rio.band(self.src, self.src.indexes),
                out,
                dst_transform=toaffine,
                dst_crs='epsg:3857',
                src_nodata=0,
                dst_nodata=0,
                resampling=Resampling.bilinear)

            # matrix = np.where(out > 0, self.__rescale_intensity__(out, in_range=[0,16000], out_range=[1, 255]), 0)
            # out = matrix.astype(np.uint8)

            if self.src.count == 3:
                if self.src.nodatavals:
                    out[-1] = np.all(np.dstack(out[:3]) != self.src.nodatavals, axis=2).astype(np.uint8) * 255
                else:
                    out[-1] = 255

            img = Image.fromarray(np.dstack(out))
            if tileformat == 'jpeg':
                img.convert('RGB')

            sio = BytesIO()
            img.save(sio, tileformat)
            sio.seek(0)

            return (200, 'image/{}'.format(tileformat), sio.read())
        except:
            return (500, 'application/json', json.dumps({"ErrorMessage": 'Error while processing the tile {}/{}/{}'.format(z,x,y)}).encode('utf-8'))

pk = Peeker()

@aiohttp_jinja2.template('index.html')
def main_page(request):
    return {'bounds': pk.get_bounds(), 'ctrlat': pk.get_ctr_lat(), 'ctrlng': pk.get_ctr_lng()}

#Get Tiles
async def tiles(request):
    x = int(request.match_info.get('x'))
    y = int(request.match_info.get('y'))
    z = int(request.match_info.get('z'))

    if not pk.tile_exists(z, x, y):
        return web.Response(
            status=204,
            body=json.dumps({"WarningMessage": 'Tile {}/{}/{} is outside image bounds'.format(z,x,y)}).encode('utf-8'),
            content_type='application/json'
        )

    response = pk.get_tile(z, x, y)
    return web.Response(status=response[0], body=response[2], content_type=response[1])

#Get Bounds
async def bounds(request):
    return web.Response(
        status=400,
        body=json.dumps(pk.get_bounds()).encode('utf-8'),
        content_type='application/json'
    )

app.router.add_get('/', main_page)
app.router.add_get('/bounds', bounds)
app.router.add_get('/tiles/{z}/{x}/{y}.png', tiles)

@click.command()
@click.argument('srcpath', type=click.Path(exists=True))
def glui(srcpath):
    pk.start(srcpath)
    click.echo('Inspecting {0} at http://127.0.0.1:5000/'.format(srcpath), err=True)
    web.run_app(app, host='127.0.0.1', port=5000)
