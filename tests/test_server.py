"""tests rio_glui.server."""

import os

from tornado.testing import AsyncHTTPTestCase

from rio_glui.raster import RasterTiles
from rio_glui.server import TileServer

raster_path = os.path.join(os.path.dirname(__file__), 'fixtures', '16-21560-29773_small_ycbcr.tif')
invalid_raster_path = os.path.join(os.path.dirname(__file__), 'fixtures', '16-21560-29773_small.tif')


def test_TileServer_default():
    """Should work as expected (create TileServer object)."""
    r = RasterTiles(raster_path)
    app = TileServer(r)
    assert app.raster == r
    assert app.port == 8080
    assert not app.server
    assert app.tiles_format == 'png'
    assert app.gl_tiles_size == 512
    assert app.gl_tiles_minzoom == 0
    assert app.gl_tiles_maxzoom == 22


def test_TileServer_options():
    """Should work as expected (create TileServer object)."""
    r = RasterTiles(raster_path)
    app = TileServer(r, tiles_format='jpg', gl_tiles_minzoom=13, gl_tiles_maxzoom=19, gl_tiles_size=256, port=5000)
    assert app.raster == r
    assert app.port == 5000
    assert not app.server
    assert app.tiles_format == 'jpg'
    assert app.gl_tiles_size == 256
    assert app.gl_tiles_minzoom == 13
    assert app.gl_tiles_maxzoom == 19


def test_TileServer_raster_tilesize():
    """Should work as expected (create TileServer object)."""
    r = RasterTiles(raster_path, tiles_size=256)
    app = TileServer(r)
    assert app.raster == r
    assert not app.server
    assert app.tiles_format == 'png'
    assert app.gl_tiles_size == 256


def test_TileServer_raster_get_bounds():
    """Should work as expected."""
    r = RasterTiles(raster_path)
    app = TileServer(r)
    assert app.raster == r
    assert app.get_bounds() == r.get_bounds()


def test_TileServer_raster_get_center():
    """Should work as expected."""
    r = RasterTiles(raster_path)
    app = TileServer(r)
    assert app.raster == r
    assert app.get_center() == r.get_center()


def test_TileServer_get_tiles_url():
    """Should work as expected (create TileServer object and get tiles endpoint)."""
    r = RasterTiles(raster_path)
    app = TileServer(r)
    assert app.get_tiles_url() == 'http://127.0.0.1:8080/tiles/{z}/{x}/{y}.png'


def test_TileServer_get_template_url():
    """Should work as expected (create TileServer object and get template url)."""
    r = RasterTiles(raster_path)
    app = TileServer(r)
    assert app.get_template_url() == 'http://127.0.0.1:8080/index.html'


def test_TileServer_get_playround_url():
    """Should work as expected (create TileServer object and get playground url)."""
    r = RasterTiles(raster_path)
    app = TileServer(r)
    assert app.get_playround_url() == 'http://127.0.0.1:8080/playground.html'


class TestHandlers(AsyncHTTPTestCase):
    """Test tornado handlers."""

    def get_app(self):
        """Initialize app."""
        r = RasterTiles(raster_path)
        return TileServer(r).app

    def test_get_root(self):
        """Should return error on root query."""
        response = self.fetch('/')
        self.assertEqual(response.code, 404)

    def test_tile(self):
        """Should return tile buffer."""
        response = self.fetch('/tiles/18/86240/119094.png')
        self.assertEqual(response.code, 200)
        self.assertTrue(response.buffer)
        self.assertEqual(response.headers['Content-Type'], 'image/png')

    def test_tileColor(self):
        """Should apply color ops and return tile buffer."""
        response = self.fetch('/tiles/18/86240/119094.png?color=gamma%20b%201.8')
        self.assertEqual(response.code, 200)
        self.assertTrue(response.buffer)
        self.assertEqual(response.headers['Content-Type'], 'image/png')

    def test_tileJpeg(self):
        """Should return tile jpeg buffer."""
        response = self.fetch('/tiles/18/86240/119094.jpg')
        self.assertEqual(response.code, 200)
        self.assertTrue(response.buffer)
        self.assertEqual(response.headers['Content-Type'], 'image/jpg')

    def test_tileNotFound(self):
        """Should error with tile doesn't exits."""
        response = self.fetch('/tiles/18/8624/119094.png')
        self.assertEqual(response.code, 404)

    def test_TemplateSimple(self):
        """Should find the template."""
        response = self.fetch('/index.html')
        self.assertEqual(response.code, 200)

    def test_TemplatePlayground(self):
        """Should find the template."""
        response = self.fetch('/playground.html')
        self.assertEqual(response.code, 200)
