"""rio_glui.server.py: tornado tile server and template rendered"""

import os
from io import BytesIO
from concurrent import futures

import numpy

from rio_tiler.utils import array_to_img
from rio_tiler import profiles as TileProfiles
from rio_color.operations import parse_operations
from rio_color.utils import scale_dtype, to_math_type

from tornado import web
from tornado import gen
from tornado.httpserver import HTTPServer
from tornado.concurrent import run_on_executor
from tornado.ioloop import IOLoop


class TileServer(object):
    """creates a very minimal slippy map tile server
    uses the jupyter notebook tornado.ioloop"""

    def __init__(self, raster, tiles_format='png', tiles_minzoom=0, tiles_maxzoom=22, tiles_size=512, port=8080):
        self.raster = raster
        self.port = port
        self.server = None
        self.tiles_size = tiles_size
        self.tiles_format = tiles_format
        self.tiles_minzoom = tiles_minzoom
        self.tiles_maxzoom = tiles_maxzoom

    def get_tiles_url(self):
        tileformat = 'jpg' if self.tiles_format == 'jpeg' else self.tiles_format
        return 'http://127.0.0.1:{}/tiles/{{z}}/{{x}}/{{y}}.{}'.format(self.port, tileformat)

    def get_template_url(self):
        return 'http://127.0.0.1:{}/index.html'.format(self.port)

    def get_playround_url(self):
        return 'http://127.0.0.1:{}/playground.html'.format(self.port)

    def start(self):

        settings = {
            "static_path": os.path.join(os.path.dirname(__file__), "static")}

        tile_params = dict(
            raster=self.raster)

        template_params = dict(
            url=self.get_tiles_url(),
            bounds=self.raster.get_bounds(),
            center=self.raster.get_center(),
            min_zoom=self.tiles_minzoom,
            max_zoom=self.tiles_maxzoom,
            size=self.tiles_size)

        application = web.Application([
            (r'^/tiles/(\d+)/(\d+)/(\d+)\.(\w+)', RasterTileHandler, tile_params),
            (r'^/index.html', IndexTemplate, template_params),
            (r'^/playground.html', PlaygroundTemplate, template_params),
            (r"/.*", ErrorHandler)], **settings)

        self.server = HTTPServer(application)
        self.server.listen(self.port)

        # Check if there is already one server in place
        # else initiate an new one
        # if not IOLoop.initialized():
        IOLoop.current().start()

    def stop(self):
        if self.server:
            self.server.stop()


class ErrorHandler(web.RequestHandler):
    def get(self):
        raise web.HTTPError(404)


class RasterTileHandler(web.RequestHandler):
    """
    """
    executor = futures.ThreadPoolExecutor(max_workers=16)

    def initialize(self, raster):
        self.raster = raster

    def _apply_color_operations(self, img, color_ops):
        """
        """
        for ops in parse_operations(color_ops):
            img = scale_dtype(ops(to_math_type(img)), numpy.uint8)

        return img

    @run_on_executor
    def _get_tile(self, z, x, y, tileformat, color_ops=None):
        """
        """
        if tileformat == 'jpg':
            tileformat = 'jpeg'

        if not self.raster.tile_exists(z, x, y):
            raise web.HTTPError(404)

        data, mask = self.raster.read_tile(z, x, y)

        if color_ops:
            data = self._apply_color_operations(data, color_ops)

        img = array_to_img(data, mask=mask)
        params = TileProfiles.get(tileformat)
        if tileformat == 'jpeg':
            img = img.convert('RGB')

        sio = BytesIO()
        img.save(sio, tileformat.upper(), **params)
        sio.seek(0)
        return sio

    @gen.coroutine
    def get(self, z, x, y, tileformat):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'GET')
        self.set_header('Content-Type', 'image/{}'.format(tileformat))
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

        color_ops = self.get_argument('color', None)

        res = yield self._get_tile(int(z), int(x), int(y), tileformat, color_ops=color_ops)
        self.write(res.getvalue())


class IndexTemplate(web.RequestHandler):
    """
    """
    def initialize(self, url, bounds, center, min_zoom, max_zoom, size):
        self.url = url
        self.bounds = bounds
        self.center = center
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.size = size

    def get(self):
        params = dict(
            tiles_bounds=self.bounds,
            center=self.center,
            tiles_url=self.url,
            zoom=self.min_zoom,
            tiles_minzoom=self.min_zoom,
            tiles_maxzoom=self.max_zoom,
            tiles_size=self.size)

        self.render('templates/index.html', **params)


class PlaygroundTemplate(web.RequestHandler):
    """
    """
    def initialize(self, url, bounds, center, min_zoom, max_zoom, size):
        self.url = url
        self.bounds = bounds
        self.center = center
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.size = size

    def get(self):
        params = dict(
            tiles_bounds=self.bounds,
            center=self.center,
            tiles_url=self.url,
            zoom=self.min_zoom,
            tiles_minzoom=self.min_zoom,
            tiles_maxzoom=self.max_zoom,
            tiles_size=self.size)

        self.render('templates/playground.html', **params)
