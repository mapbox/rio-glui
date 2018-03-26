"""tests rio_glui.raster."""

import os
import pytest
#
# from mock import patch

from rio_glui.raster import RasterTiles, _meters_per_pixel

raster_path = os.path.join(os.path.dirname(__file__), 'fixtures', '16-21560-29773_small_ycbcr.tif')
invalid_raster_path = os.path.join(os.path.dirname(__file__), 'fixtures', '16-21560-29773_small.tif')


def test_meters_per_pixel_valid():
    """Should work as expected (returns correct pixel size)."""
    assert _meters_per_pixel(18, 45) == 0.4222589143296568
    assert _meters_per_pixel(18, -45) == 0.4222589143296568


def test_rastertiles_valid():
    """Should work as expected (create rastertiles object)."""
    r = RasterTiles(raster_path)
    assert r.path == raster_path
    assert r.tiles_size == 512
    assert not r.alpha
    assert not r.nodata
    assert r.bounds == [-61.56738281249997, 16.225223624120076, -61.5618896507246, 16.23049792684362]
    assert r.indexes == (1, 2, 3)
    assert r.overiew_levels == [2, 4, 8, 16, 32, 64]


def test_rastertiles_invalidcogeo():
    """Should error with invalid Cogeo format."""
    with pytest.raises(Exception):
        RasterTiles(invalid_raster_path)


def test_rastertiles_valid_indexes_option():
    """Should work as expected (create rastertiles object)."""
    r = RasterTiles(raster_path, indexes=[1])
    assert r.path == raster_path
    assert r.indexes == [1]
    assert r.tiles_size == 512
    assert not r.alpha
    assert not r.nodata


def test_rastertiles_valid_size_option():
    """Should work as expected (create rastertiles object)."""
    r = RasterTiles(raster_path, tiles_size=256)
    assert r.path == raster_path
    assert r.tiles_size == 256
    assert not r.alpha
    assert not r.nodata


def test_rastertiles_valid_nodata_option():
    """Should work as expected (create rastertiles object)."""
    r = RasterTiles(raster_path, nodata=0)
    assert r.path == raster_path
    assert r.nodata == 0
    assert not r.alpha


def test_rastertiles_valid_alpha_option():
    """Should work as expected (create rastertiles object)."""
    r = RasterTiles(raster_path, alpha=3)
    assert r.path == raster_path
    assert r.alpha == 3
    assert not r.nodata


def test_rastertiles_get_bounds():
    """Should work as expected (create rastertiles object and get bounds)."""
    r = RasterTiles(raster_path)
    assert r.get_bounds() == [-61.56738281249997, 16.225223624120076, -61.5618896507246, 16.23049792684362]


def test_rastertiles_get_centers():
    """Should work as expected (create rastertiles object and get center)."""
    r = RasterTiles(raster_path)
    assert r.get_center() == [-61.56463623161228, 16.227860775481847]


def test_rastertiles_tile_exists_valid():
    """Should work as expected (create rastertiles object and check if tile exists)."""
    r = RasterTiles(raster_path)
    z = 18
    x = 86240
    y = 119094
    assert r.tile_exists(z, x, y)


def test_rastertiles_tile_exists_false():
    """Should work as expected (create rastertiles object and check if tile exists)."""
    r = RasterTiles(raster_path)
    z = 18
    x = 8240
    y = 119094
    assert not r.tile_exists(z, x, y)


def test_rastertiles_get_max_zoom():
    """Should work as expected (create rastertiles object and get_max_zoom)."""
    r = RasterTiles(raster_path)
    assert r.get_max_zoom() == 19


def test_rastertiles_get_min_zoom():
    """Should work as expected (create rastertiles object and get_min_zoom)."""
    r = RasterTiles(raster_path)
    assert r.get_min_zoom() == 12


def test_rastertiles_read_tile():
    """Should work as expected (create rastertiles object and read tile)."""
    r = RasterTiles(raster_path)
    z = 18
    x = 86240
    y = 119094
    data, mask = r.read_tile(z, x, y)
    assert data.shape == (3, 512, 512)
    assert mask.shape == (512, 512)


def test_rastertiles_read_tile_small():
    """Should work as expected (create rastertiles object and read tile)."""
    r = RasterTiles(raster_path, tiles_size=256)
    z = 18
    x = 86240
    y = 119094
    data, mask = r.read_tile(z, x, y)
    assert data.shape == (3, 256, 256)
    assert mask.shape == (256, 256)
