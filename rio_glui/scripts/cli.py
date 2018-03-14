"""rio_glui.cli"""

import os
import click

from rio_glui.raster import RasterTiles
from rio_glui.server import TileServer


class CustomType():
    class MbxTokenType(click.ParamType):
        """Mapbox Token Type
        """
        name = 'str'

        def convert(self, value, param, ctx):
            try:
                if not value:
                    return ''
                assert value.startswith('pk')
                return value
            except (AttributeError, AssertionError):
                raise click.ClickException('Mapbox access token must be public (pk). '
                                           'Please sign up at https://www.mapbox.com/signup/ to get a public token. '
                                           'If you already have an account, you can retreive your '
                                           'token at https://www.mapbox.com/account/.')

    class BdxParamType(click.ParamType):
        """Band Index Type
        """
        name = 'str'

        def convert(self, value, param, ctx):
            try:
                bands = [int(x) for x in value.split(',')]
                assert len(bands) in [1, 3]
                assert all(b > 0 for b in bands)
                return value
            except (AttributeError, AssertionError):
                raise click.ClickException('bidx must be a string with 1 or 3 ints comma-separated, '
                                           'representing the band indexes for R,G,B')

    mbxToken = MbxTokenType()
    bidx = BdxParamType()


@click.command()
@click.argument('path', type=str)
@click.option('--bidx', '-b', type=CustomType.bidx, default='1,2,3', help="Raster band index (default: 1,2,3)")
@click.option('--tiles-format', type=str, default='png', help="Tile image format (default: png)")
@click.option('--tiles-dimensions', type=int, default=512, help="Dimension of images being served (default: 512)")
@click.option('--nodata', type=int, help="")
@click.option('--alpha', type=int, help="")
@click.option('--gl-tile-size', type=int, default=512, help="mapbox-gl tileSize (default: 512)")
@click.option('--port', type=int, default=8080, help="Webserver port (default: 8080)")
@click.option('--playground', is_flag=True, help="Launch playground app")
@click.option('--mapbox-token', type=CustomType.mbxToken,
              default=lambda: os.environ.get('MAPBOX_ACCESS_TOKEN', ''),
              help="Launch playground app")
def glui(path, bidx, tiles_format, tiles_dimensions, nodata, alpha, gl_tile_size, port, playground, mapbox_token):
    """
    """
    raster = RasterTiles(path, bidx=bidx, tiles_size=tiles_dimensions, nodata=nodata, alpha=alpha)
    app = TileServer(raster, tiles_size=gl_tile_size, tiles_format=tiles_format)

    if playground:
        url = app.get_playround_url()
    else:
        url = app.get_template_url()

    if mapbox_token:
        url = '{}?access_token={}'.format(url, mapbox_token)

    click.launch(url)
    click.echo('Inspecting {} at {}/'.format(path, url), err=True)
    app.start()
