"""rio_glui.raster: raster tiles object"""

import math

import mercantile
import rasterio
from rasterio.warp import transform_bounds, calculate_default_transform

from rio_tiler.main import tile


class RasterTiles(object):
    """
    """
    def __init__(self, path, bidx=None, tiles_size=512, nodata=None, alpha=None):
        self.path = path
        self.size = tiles_size
        self.alpha = alpha
        self.nodata = nodata

        if bidx:
            bidx = [int(b) for b in bidx.split(',')]

        # TODO: Check if the raster is a CloudOptimized Geotiff
        # - GeoTiff
        # - internal tiling
        # - uint8
        # - overviews

        with rasterio.open(path) as src:
            self.bounds = list(transform_bounds(*[src.crs, 'epsg:4326'] + list(src.bounds), densify_pts=0))
            self.indexes = bidx if bidx is not None else src.indexes
            self.nodata = self.nodata if self.nodata else src.nodata

    def get_bounds(self):
        return list(self.bounds)

    def get_center(self):
        lat = (self.bounds[3] - self.bounds[1]) / 2 + self.bounds[1]
        lng = (self.bounds[2] - self.bounds[0]) / 2 + self.bounds[0]
        return [lng, lat]

    def tile_exists(self, z, x, y):
        mintile = mercantile.tile(self.bounds[0], self.bounds[3], z)
        maxtile = mercantile.tile(self.bounds[2], self.bounds[1], z)
        return (x <= maxtile.x + 1) and (x >= mintile.x) and (y <= maxtile.y + 1) and (y >= mintile.y)

    def _meters_per_pixel(self, zoom, lat):
        return (math.cos(lat * math.pi/180.0) * 2 * math.pi * 6378137) / (256 * 2**zoom)

    def get_max_zoom(self, snap=0.5, max_z=23):

        with rasterio.open(self.path) as src:
            dst_affine, width, height = calculate_default_transform(src.crs,
                                                                    'epsg:3857',
                                                                    src.meta['width'],
                                                                    src.meta['height'],
                                                                    *src.bounds)

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

    def get_min_zoom(self, snap=0.5, max_z=24):

        with rasterio.open(self.path) as src:
            dst_affine, width, height = calculate_default_transform(src.crs,
                                                                    'epsg:3857',
                                                                    src.meta['width'],
                                                                    src.meta['height'],
                                                                    *src.bounds)

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
        return tile(self.path, x, y, z, rgb=self.indexes, tilesize=self.size,
                    nodata=self.nodata, alpha=self.alpha)
