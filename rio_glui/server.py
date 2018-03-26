"""rio_glui.server: tornado tile server and template renderer."""

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
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.concurrent import run_on_executor


class TileServer(object):
    """
    Creates a very minimal slippy map tile server using tornado.ioloop.

    Attributes
    ----------
    raster : RasterTiles
        Rastertiles object.
    tiles_format : str, optional
        Tile image format.
    tiles_minzoom: int, optional (default: 0)
        Raster tile minimun zoom.
    tiles_maxzoom, int, optional (default: 22)
        Raster tile maximun zoom.
    tiles_size, int, optional (default: 512)
        Tile pixel size.
    port, int, optional (default: 8080)
        Tornado app default port.


    Methods
    -------
    get_tiles_url()
        Get tiles endpoint url.
    get_template_url()
        Get simple app template url.
    get_playround_url()
        Get playground app template url.
    start()
        Start tile server.
    stop()
        Stop tile server.

    """

    def __init__(self, raster, tiles_format='png', tiles_minzoom=0, tiles_maxzoom=22, tiles_size=512, port=8080):
        """Initialize Tornado app."""
        self.raster = raster
        self.port = port
        self.server = None
        self.tiles_size = tiles_size
        self.tiles_format = tiles_format
        self.tiles_minzoom = tiles_minzoom
        self.tiles_maxzoom = tiles_maxzoom

    def get_tiles_url(self):
        """Get tiles endpoint url."""
        tileformat = 'jpg' if self.tiles_format == 'jpeg' else self.tiles_format
        return 'http://127.0.0.1:{}/tiles/{{z}}/{{x}}/{{y}}.{}'.format(self.port, tileformat)

    def get_template_url(self):
        """Get simple app template url."""
        return 'http://127.0.0.1:{}/index.html'.format(self.port)

    def get_playround_url(self):
        """Get playground app template url."""
        return 'http://127.0.0.1:{}/playground.html'.format(self.port)

    def start(self):
        """Start tile server."""
        settings = {
            "static_path": os.path.join(os.path.dirname(__file__), "static")}

        tile_params = dict(
            raster=self.raster)

        template_params = dict(
            tiles_url=self.get_tiles_url(),
            tiles_bounds=self.raster.get_bounds(),
            tiles_minzoom=self.tiles_minzoom,
            tiles_maxzoom=self.tiles_maxzoom,
            tiles_size=self.tiles_size)

        application = web.Application([
            (r'^/tiles/(\d+)/(\d+)/(\d+)\.(\w+)', RasterTileHandler, tile_params),
            (r'^/index.html', IndexTemplate, template_params),
            (r'^/playground.html', PlaygroundTemplate, template_params),
            (r"/.*", InvalidAddress)], **settings)

        is_running = IOLoop.initialized()
        self.server = HTTPServer(application)
        self.server.listen(self.port)

        # Check if there is already one server in place
        # else initiate an new one
        if not is_running:
            IOLoop.current().start()

    def stop(self):
        """Stop tile server."""
        if self.server:
            self.server.stop()


class InvalidAddress(web.RequestHandler):
    """Invalid web requests handler."""

    def get(self):
        """Retunrs 404 error."""
        raise web.HTTPError(404)


class RasterTileHandler(web.RequestHandler):
    """
    RasterTiles requests handler.

    Attributes
    ----------
    raster : RasterTiles
        Rastertiles object.

    Methods
    -------
    initialize()
        Initialize tiles handler.
    get()
        Get tile data and mask.

    """

    executor = futures.ThreadPoolExecutor(max_workers=16)

    def initialize(self, raster):
        """Initialize tiles handler."""
        self.raster = raster

    def _apply_color_operations(self, img, color_ops):
        for ops in parse_operations(color_ops):
            img = scale_dtype(ops(to_math_type(img)), numpy.uint8)

        return img

    @run_on_executor
    def _get_tile(self, z, x, y, tileformat, color_ops=None):
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
        """Retunrs tile data and header."""
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'GET')
        self.set_header('Content-Type', 'image/{}'.format(tileformat))
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

        color_ops = self.get_argument('color', None)

        res = yield self._get_tile(int(z), int(x), int(y), tileformat, color_ops=color_ops)
        self.write(res.getvalue())


class Template(web.RequestHandler):
    """
    Template requests handler.

    Attributes
    ----------
    tiles_url : str
        Tiles endpoint url.
    tiles_bounds : tuple, list
        Tiles source bounds [maxlng, maxlat, minlng, minlat].
    tiles_minzoom = tiles_minzoom
        Tiles source minimun zoom level.
    tiles_maxzoom = tiles_maxzoom
        Tiles source maximum zoom level.
    tiles_size = tiles_size
        Tiles pixel size.

    Methods
    -------
    initialize()
        Initialize template handler.

    """

    def initialize(self, tiles_url, tiles_bounds, tiles_minzoom, tiles_maxzoom, tiles_size):
        """Initialize template handler."""
        self.tiles_url = tiles_url
        self.tiles_bounds = tiles_bounds
        self.tiles_minzoom = tiles_minzoom
        self.tiles_maxzoom = tiles_maxzoom
        self.tiles_size = tiles_size


class IndexTemplate(Template):
    """Index template."""

    def get(self):
        """Get template."""
        params = dict(
            tiles_bounds=self.tiles_bounds,
            tiles_url=self.tiles_url,
            tiles_minzoom=self.tiles_minzoom,
            tiles_maxzoom=self.tiles_maxzoom,
            tiles_size=self.tiles_size)

        self.render('templates/index.html', **params)


class PlaygroundTemplate(Template):
    """Playground template."""

    def get(self):
        """Get template."""
        params = dict(
            tiles_bounds=self.tiles_bounds,
            tiles_url=self.tiles_url,
            tiles_minzoom=self.tiles_minzoom,
            tiles_maxzoom=self.tiles_maxzoom,
            tiles_size=self.tiles_size)

        self.render('templates/playground.html', **params)
