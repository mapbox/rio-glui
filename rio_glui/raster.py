"""rio_glui.raster: raster tiles object."""

import math

import mercantile
import rasterio
from rasterio.warp import transform_bounds, calculate_default_transform

from rio_tiler.main import tile


class RasterTiles(object):
    """
    Raster tiles object.

    Attributes
    ----------
    path : str
        Raster data file path.
    indexes : tuple, int, optional
        Raster band indexes to read.
    tiles_size: int, optional (default: 512)
        X/Y tile size to return.
    nodata, int, optional
        nodata value for mask creation.
    alpha, int, optional
        alpha band index for mask creation.

    Methods
    -------
    get_bounds()
        Get raster bounds (WGS84).
    get_center()
        Get raster lon/lat center coordinates.
    tile_exists(z, x, y)
        Check if a mercator tile is within raster bounds.
    get_max_zoom(snap=0.5, max_z=23)
        Calculate raster max zoom level.
    get_min_zoom(snap=0.5, max_z=23)
        Calculate raster min zoom level.
    read_tile( z, x, y)
        Read raster tile data and mask.

    """

    def __init__(self, path, indexes=None, tiles_size=512, nodata=None, alpha=None):
        """Initialize RasterTiles object."""
        self.path = path
        self.size = tiles_size
        self.alpha = alpha
        self.nodata = nodata

        with rasterio.open(path) as src:

            try:
                assert src.driver == 'GTiff'
                assert src.is_tiled
                assert src.overviews(1)
            except (AttributeError, AssertionError, KeyError):
                raise Exception('{} is not a valid CloudOptimized Geotiff'.format(path))

            self.bounds = list(transform_bounds(*[src.crs, 'epsg:4326'] + list(src.bounds), densify_pts=0))
            self.indexes = indexes if indexes is not None else src.indexes

    def get_bounds(self):
        """Get raster bounds (WGS84)."""
        return list(self.bounds)

    def get_center(self):
        """Get raster lon/lat center coordinates."""
        lat = (self.bounds[3] - self.bounds[1]) / 2 + self.bounds[1]
        lng = (self.bounds[2] - self.bounds[0]) / 2 + self.bounds[0]
        return [lng, lat]

    def tile_exists(self, z, x, y):
        """Check if a mercator tile is within raster bounds."""
        mintile = mercantile.tile(self.bounds[0], self.bounds[3], z)
        maxtile = mercantile.tile(self.bounds[2], self.bounds[1], z)
        return (x <= maxtile.x + 1) and (x >= mintile.x) and (y <= maxtile.y + 1) and (y >= mintile.y)

    def _meters_per_pixel(self, zoom, lat):
        return (math.cos(lat * math.pi/180.0) * 2 * math.pi * 6378137) / (256 * 2**zoom)

    def get_max_zoom(self, snap=0.5, max_z=23):
        """Calculate raster max zoom level."""
        with rasterio.open(self.path) as src:
            dst_affine, w, h = calculate_default_transform(src.crs, 'epsg:3857',
                                                           src.meta['width'], src.meta['height'], *src.bounds)

        res_max = max(abs(dst_affine[0]), abs(dst_affine[4]))

        tgt_z = max_z
        mpp = 0.0

        # loop through the pyramid to file the closest z level
        for z in range(1, max_z):
            mpp = self._meters_per_pixel(z, 0)

            if (mpp - ((mpp / 2) * snap)) < res_max:
                tgt_z = z
                break

        return tgt_z

    def get_min_zoom(self, snap=0.5, max_z=23):
        """Calculate raster min zoom level."""
        with rasterio.open(self.path) as src:
            dst_affine, w, h = calculate_default_transform(src.crs, 'epsg:3857',
                                                           src.meta['width'], src.meta['height'], *src.bounds)

            res_max = max(abs(dst_affine[0]), abs(dst_affine[4]))
            max_decim = src.overviews(1)[-1]
            resolution = max_decim * res_max

        tgt_z = 0
        mpp = 0.0

        # loop through the pyramid to file the closest z level
        for z in list(range(0, 24))[::-1]:
            mpp = self._meters_per_pixel(z, 0)
            tgt_z = z

            if (mpp - ((mpp / 2) * snap)) > resolution:
                break

        return tgt_z

    def read_tile(self, z, x, y):
        """Read raster tile data and mask."""
        return tile(self.path, x, y, z, rgb=self.indexes, tilesize=self.size,
                    nodata=self.nodata, alpha=self.alpha)
