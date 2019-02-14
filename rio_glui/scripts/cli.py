"""rio_glui.cli."""

import os
import click
import numpy

from rio_glui.raster import RasterTiles
from rio_glui import server


class MbxTokenType(click.ParamType):
    """Mapbox token type."""

    name = "token"

    def convert(self, value, param, ctx):
        """Validate token."""
        try:
            if not value:
                return ""

            assert value.startswith("pk")
            return value

        except (AttributeError, AssertionError):
            raise click.ClickException(
                "Mapbox access token must be public (pk). "
                "Please sign up at https://www.mapbox.com/signup/ to get a public token. "
                "If you already have an account, you can retreive your "
                "token at https://www.mapbox.com/account/."
            )


class BdxParamType(click.ParamType):
    """Band inddex type."""

    name = "bidx"

    def convert(self, value, param, ctx):
        """Validate and parse band index."""
        try:
            bands = [int(x) for x in value.split(",")]
            assert len(bands) in [1, 3]
            assert all(b > 0 for b in bands)
            return bands

        except (ValueError, AttributeError, AssertionError):
            raise click.ClickException(
                "bidx must be a string with 1 or 3 ints comma-separated, "
                "representing the band indexes for R,G,B"
            )


class NodataParamType(click.ParamType):
    """Nodata inddex type."""

    name = "nodata"

    def convert(self, value, param, ctx):
        """Validate and parse band index."""
        try:
            if value.lower() == "nan":
                return numpy.nan
            elif value.lower() in ["nil", "none", "nada"]:
                return None
            else:
                return float(value)
        except (TypeError, ValueError):
            raise click.ClickException("{} is not a valid nodata value.".format(value))


@click.command()
@click.argument("path", type=str)
@click.option("--bidx", "-b", type=BdxParamType(), help="Raster band index")
@click.option(
    "--scale",
    type=int,
    multiple=True,
    nargs=2,
    help="Min and Max data bounds to rescale data from. "
    "Form multiband you can either provide use '--scale 0 1000' or "
    "'--scale 0 1000 --scale 0 500 --scale 0 1500'",
)
@click.option(
    "--colormap",
    type=click.Choice(["cfastie", "schwarzwald"]),
    help=" Rio-tiler compatible colormap name",
)
@click.option(
    "--tiles-format",
    type=click.Choice(["png", "jpg", "webp"]),
    default="png",
    help="Tile image format (default: png)",
)
@click.option(
    "--tiles-dimensions",
    type=int,
    default=512,
    help="Dimension of images being served (default: 512)",
)
@click.option(
    "--nodata",
    type=NodataParamType(),
    metavar="NUMBER|nan",
    help="Set nodata masking values for input dataset.",
)
@click.option(
    "--gl-tile-size",
    type=int,
    help="mapbox-gl tileSize (default is the same as `tiles-dimensions`)",
)
@click.option("--port", type=int, default=8080, help="Webserver port (default: 8080)")
@click.option("--playground", is_flag=True, help="Launch playground app")
@click.option(
    "--mapbox-token",
    type=MbxTokenType(),
    metavar="TOKEN",
    default=lambda: os.environ.get("MAPBOX_ACCESS_TOKEN", ""),
    help="Pass Mapbox token",
)
def glui(
    path,
    bidx,
    scale,
    colormap,
    tiles_format,
    tiles_dimensions,
    nodata,
    gl_tile_size,
    port,
    playground,
    mapbox_token,
):
    """Rasterio glui cli."""
    if scale and len(scale) not in [1, 3]:
        raise click.ClickException("Invalid number of scale values")

    raster = RasterTiles(path, indexes=bidx, tiles_size=tiles_dimensions, nodata=nodata)

    app = server.TileServer(
        raster,
        scale=scale,
        colormap=colormap,
        tiles_format=tiles_format,
        gl_tiles_size=gl_tile_size,
        gl_tiles_minzoom=raster.get_min_zoom(),
        gl_tiles_maxzoom=raster.get_max_zoom(),
        port=port,
    )

    if playground:
        url = app.get_playground_url()
    else:
        url = app.get_template_url()

    if mapbox_token:
        url = "{}?access_token={}".format(url, mapbox_token)

    click.launch(url)
    click.echo("Inspecting {} at {}".format(path, url), err=True)
    app.start()
