"""rio_glui.raster: raster tiles object."""

import math

import mercantile
import rasterio
from rasterio.warp import transform_bounds, calculate_default_transform

from rio_tiler.utils import tile_read


def _meters_per_pixel(zoom, lat):
    return (math.cos(lat * math.pi / 180.0) * 2 * math.pi * 6378137) / (256 * 2 ** zoom)


class RasterTiles(object):
    """
    Raster tiles object.

    Attributes
    ----------
    src_path : str or PathLike object
        A dataset path or URL. Will be opened in "r" mode.
    indexes : tuple, int, optional
        Raster band indexes to read.
    tiles_size: int, optional (default: 512)
        X/Y tile size to return.
    nodata: int, optional
        nodata value for mask creation.

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

    def __init__(self, src_path, indexes=None, tiles_size=512, nodata=None):
        """Initialize RasterTiles object."""
        self.path = src_path
        self.tiles_size = tiles_size
        self.nodata = nodata

        with rasterio.open(src_path) as src:
            try:
                assert src.driver == "GTiff"
                assert src.is_tiled
                assert src.overviews(1)
            except (AttributeError, AssertionError, KeyError):
                raise Exception(
                    "{} is not a valid CloudOptimized Geotiff".format(src_path)
                )

            self.bounds = list(
                transform_bounds(
                    *[src.crs, "epsg:4326"] + list(src.bounds), densify_pts=0
                )
            )
            self.indexes = indexes if indexes is not None else src.indexes
            self.crs = src.crs
            self.crs_bounds = src.bounds
            self.meta = src.meta
            self.overiew_levels = src.overviews(1)

    def get_bounds(self):
        """Get raster bounds (WGS84)."""
        return self.bounds

    def get_center(self):
        """Get raster lon/lat center coordinates."""
        lat = (self.bounds[3] - self.bounds[1]) / 2 + self.bounds[1]
        lng = (self.bounds[2] - self.bounds[0]) / 2 + self.bounds[0]
        return [lng, lat]

    def tile_exists(self, z, x, y):
        """Check if a mercator tile is within raster bounds."""
        mintile = mercantile.tile(self.bounds[0], self.bounds[3], z)
        maxtile = mercantile.tile(self.bounds[2], self.bounds[1], z)
        return (
            (x <= maxtile.x + 1)
            and (x >= mintile.x)
            and (y <= maxtile.y + 1)
            and (y >= mintile.y)
        )

    def get_max_zoom(self, snap=0.5, max_z=23):
        """Calculate raster max zoom level."""
        dst_affine, w, h = calculate_default_transform(
            self.crs,
            "epsg:3857",
            self.meta["width"],
            self.meta["height"],
            *self.crs_bounds
        )

        res_max = max(abs(dst_affine[0]), abs(dst_affine[4]))

        tgt_z = max_z
        mpp = 0.0

        # loop through the pyramid to file the closest z level
        for z in range(1, max_z):
            mpp = _meters_per_pixel(z, 0)

            if (mpp - ((mpp / 2) * snap)) < res_max:
                tgt_z = z
                break

        return tgt_z

    def get_min_zoom(self, snap=0.5, max_z=23):
        """Calculate raster min zoom level."""
        dst_affine, w, h = calculate_default_transform(
            self.crs,
            "epsg:3857",
            self.meta["width"],
            self.meta["height"],
            *self.crs_bounds
        )

        res_max = max(abs(dst_affine[0]), abs(dst_affine[4]))
        max_decim = self.overiew_levels[-1]
        resolution = max_decim * res_max

        tgt_z = 0
        mpp = 0.0

        # loop through the pyramid to file the closest z level
        for z in list(range(0, 24))[::-1]:
            mpp = _meters_per_pixel(z, 0)
            tgt_z = z

            if (mpp - ((mpp / 2) * snap)) > resolution:
                break

        return tgt_z

    def read_tile(self, z, x, y):
        """Read raster tile data and mask."""
        mercator_tile = mercantile.Tile(x=x, y=y, z=z)
        tile_bounds = mercantile.xy_bounds(mercator_tile)
        return tile_read(
            self.path,
            tile_bounds,
            self.tiles_size,
            indexes=self.indexes,
            nodata=self.nodata,
        )
