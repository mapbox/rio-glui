"""tests rio_glui.server."""

import os
import pytest

from mock import patch

from click.testing import CliRunner

from rio_glui.scripts.cli import glui

raster_path = os.path.join(
    os.path.dirname(__file__), "fixtures", "16-21560-29773_small_ycbcr.tif"
)

raster_ndvi_path = os.path.join(os.path.dirname(__file__), "fixtures", "ndvi_cogeo.tif")


@pytest.fixture(autouse=True)
def testing_env_var(monkeypatch):
    """Set testing env variable."""
    monkeypatch.delenv("MAPBOX_ACCESS_TOKEN", raising=False)


@patch("rio_glui.server.TileServer")
@patch("click.launch")
def test_glui_valid(launch, TileServer):
    """Should work as expected."""
    TileServer.return_value.get_template_url.return_value = (
        "http://127.0.0.1:8080/index.html"
    )
    TileServer.return_value.start.return_value = True

    launch.return_value = True

    runner = CliRunner()
    result = runner.invoke(glui, [raster_path])
    TileServer.assert_called_once()
    assert not result.exception
    assert result.exit_code == 0


@patch("rio_glui.server.TileServer")
@patch("click.launch")
def test_glui_validbidx(launch, TileServer):
    """Should work as expected."""
    TileServer.return_value.get_template_url.return_value = (
        "http://127.0.0.1:8080/index.html"
    )
    TileServer.return_value.start.return_value = True

    launch.return_value = True

    runner = CliRunner()
    result = runner.invoke(glui, [raster_path, "--bidx", "1,2,3"])
    TileServer.assert_called_once()
    assert not result.exception
    assert result.exit_code == 0


@patch("rio_glui.server.TileServer")
@patch("click.launch")
def test_glui_valid_playground(launch, TileServer):
    """Should work as expected."""
    TileServer.return_value.get_playround_url.return_value = (
        "http://127.0.0.1:8080/playground.html"
    )
    TileServer.return_value.start.return_value = True

    launch.return_value = True

    runner = CliRunner()
    result = runner.invoke(glui, [raster_path, "--playground"])
    TileServer.assert_called_once()
    assert not result.exception
    assert result.exit_code == 0


@patch("rio_glui.server.TileServer")
@patch("click.launch")
def test_glui_validEnvToken(launch, TileServer, monkeypatch):
    """Should work as expected."""
    monkeypatch.setenv("MAPBOX_ACCESS_TOKEN", "pk.afakemapboxtoken")

    TileServer.return_value.get_template_url.return_value = (
        "http://127.0.0.1:8080/index.html"
    )
    TileServer.return_value.start.return_value = True

    launch.return_value = True

    runner = CliRunner()
    result = runner.invoke(glui, [raster_path])
    TileServer.assert_called_once()
    assert not result.exception
    assert result.exit_code == 0


@patch("rio_glui.server.TileServer")
@patch("click.launch")
def test_glui_validToken(launch, TileServer):
    """Should work as expected."""
    TileServer.return_value.get_template_url.return_value = (
        "http://127.0.0.1:8080/index.html"
    )
    TileServer.return_value.start.return_value = True

    launch.return_value = True

    runner = CliRunner()
    result = runner.invoke(glui, [raster_path, "--mapbox-token", "pk.afakemapboxtoken"])
    TileServer.assert_called_once()
    assert not result.exception
    assert result.exit_code == 0


@patch("rio_glui.server.TileServer")
@patch("click.launch")
def test_glui_validInvalidToken(launch, TileServer):
    """Should work as expected."""
    runner = CliRunner()
    result = runner.invoke(glui, [raster_path, "--mapbox-token", "sk.afakemapboxtoken"])
    TileServer.assert_not_called()
    launch.assert_not_called()
    assert result.exception
    assert result.exit_code == 1


@patch("rio_glui.server.TileServer")
@patch("click.launch")
def test_glui_validInvalidbidx(launch, TileServer):
    """Should work as expected."""
    runner = CliRunner()
    result = runner.invoke(glui, [raster_path, "--bidx", "1,a,2"])
    TileServer.assert_not_called()
    launch.assert_not_called()
    assert result.exception
    assert result.exit_code == 1


@patch("rio_glui.server.TileServer")
@patch("click.launch")
def test_glui_validInvalidbidxLength(launch, TileServer):
    """Should work as expected."""
    runner = CliRunner()
    result = runner.invoke(glui, [raster_path, "--bidx", "1,2"])
    TileServer.assert_not_called()
    launch.assert_not_called()
    assert result.exception
    assert result.exit_code == 1


@patch("rio_glui.server.TileServer")
@patch("click.launch")
def test_glui_validInvalidbidxZero(launch, TileServer):
    """Should work as expected."""
    runner = CliRunner()
    result = runner.invoke(glui, [raster_path, "--bidx", "0"])
    TileServer.assert_not_called()
    launch.assert_not_called()
    assert result.exception
    assert result.exit_code == 1


@patch("rio_glui.server.TileServer")
@patch("click.launch")
def test_glui_validScaleColorMap(launch, TileServer):
    """Should work as expected."""
    TileServer.return_value.get_template_url.return_value = (
        "http://127.0.0.1:8080/index.html"
    )
    TileServer.return_value.start.return_value = True

    launch.return_value = True

    runner = CliRunner()
    result = runner.invoke(
        glui, [raster_ndvi_path, "--scale", "-1", "1", "--colormap", "cfastie"]
    )
    TileServer.assert_called_once()
    assert not result.exception
    assert result.exit_code == 0


@patch("rio_glui.server.TileServer")
@patch("click.launch")
def test_glui_invalidScale(launch, TileServer):
    """Should work as expected."""
    TileServer.return_value.get_template_url.return_value = (
        "http://127.0.0.1:8080/index.html"
    )
    TileServer.return_value.start.return_value = True

    launch.return_value = True

    runner = CliRunner()
    result = runner.invoke(glui, [raster_ndvi_path, "--scale", "-1"])
    TileServer.assert_not_called()
    launch.assert_not_called()
    assert result.exception
    assert result.exit_code == 2


@patch("rio_glui.server.TileServer")
@patch("click.launch")
def test_glui_invalidScaleNumber(launch, TileServer):
    """Should work as expected."""
    TileServer.return_value.get_template_url.return_value = (
        "http://127.0.0.1:8080/index.html"
    )
    TileServer.return_value.start.return_value = True

    launch.return_value = True

    runner = CliRunner()
    result = runner.invoke(
        glui, [raster_ndvi_path, "--scale", "-1", "1", "--scale", "0", "1"]
    )
    TileServer.assert_not_called()
    launch.assert_not_called()
    assert result.exception
    assert result.exit_code == 1
