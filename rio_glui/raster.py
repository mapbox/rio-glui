"""rio_glui.raster: raster tiles object"""

import mercantile
import rasterio
from rasterio.warp import transform_bounds

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

    def read_tile(self, z, x, y):
        return tile(self.path, x, y, z, rgb=self.indexes, tilesize=self.size,
                    nodata=self.nodata, alpha=self.alpha)
