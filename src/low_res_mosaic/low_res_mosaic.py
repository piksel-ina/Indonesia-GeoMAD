# Adapted from https://github.com/digitalearthafrica/deafrica-scripts/blob/main/deafrica/data/create_mosaic.py
import json
from calendar import monthrange
from typing import Tuple
from xarray import DataArray, Dataset

import click
import pystac
from datacube import Datacube
from datacube.utils.dask import start_local_dask
from odc.geo.cog import save_cog_with_dask
from odc.aws import s3_client, s3_dump, s3_head_object
from pystac.asset import Asset
from rio_stac import create_stac_item

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("low_res_mosaic")


def _save_opinionated_cog(
    dataset: Dataset, out_file: str, band: str | None = None, roles: list[str] = ["data"]
) -> Asset:
    data_array: DataArray
    if band is not None:
        data_array = dataset[band].squeeze("time")
    else:
        data_array = dataset.squeeze("time").to_stacked_array("bands", ["x", "y"])

    # Use default compression because we want lossless.
    cog = save_cog_with_dask(
        data_array,
        out_file,
        blocksize=1024,
        overview_resampling="average",
        bigtiff=True,
        stats=True,
    )

    cog.compute()

    return pystac.Asset(media_type=pystac.MediaType.COG, href=out_file, roles=roles)


def _get_path(s3_output_root: str, version: str, out_product: str, time_str: str, ext: str, band: str | None = None):
    base = f"{s3_output_root}/{out_product}/{version}/{time_str}/{out_product}_{time_str}"
    if band is None:
        return f"{base}.{ext}"
    else:
        return f"{base}_{band}.{ext}"


def _time_bounds(time_start: str, period: str) -> Tuple[Tuple[str, str], str]:
    """Turn a --time-start/--period pair into a (start, end) date tuple and a time_str label."""
    if period not in ["P1Y", "P6M"]:
        log.exception(f"Time period {period} not supported, please use one of P1Y or P6M")
        exit(1)

    time_str = f"{time_start}--{period}"
    if period == "P1Y":
        time = (f"{time_start}-01-01", f"{time_start}-12-31")
    else:  # P6M
        year, start_month = [int(s) for s in time_start.split("-")]
        end_month = start_month + 5
        end_month_n_days = monthrange(year, end_month)[1]
        time = (
            f"{year}-{start_month:02d}-01",
            f"{year}-{end_month:02d}-{end_month_n_days}",
        )
    return time, time_str


def create_band_cog(
    dc: Datacube,
    product: str,
    out_product: str,
    version: str,
    time: Tuple[str, str],
    time_str: str,
    band: str,
    s3_output_root: str,
    resolution: int,
    overwrite: bool,
):
    """Load a single band and write it out as its own COG. This is the unit of work that gets
    fanned out in parallel, one invocation per band."""
    log.info(f"Creating band COG for {product}/{version}/{band} over {time}")

    out_file = _get_path(s3_output_root, version, out_product, time_str, "tif", band=band)
    exists = s3_head_object(out_file) is not None
    if exists and not overwrite:
        log.info(f"File exists, and overwrite is False. Not writing {out_file}")
        return pystac.Asset(media_type=pystac.MediaType.COG, href=out_file, roles=["data"])

    start_local_dask()

    data: Dataset = dc.load(
        product=product,
        time=time,
        resolution=(-resolution, resolution),
        dask_chunks={"x": 2048, "y": 2048},
        measurements=[band],
    )


    # Just a count for information.
    datasets = list(dc.find_datasets(product=product, time=time))
    log.info(f"Found {len(datasets)} datasets for {product}/{version} over {time}")

    log.info(f"File doesn't exist, or overwrite is True. Processing and will write {out_file}")
    try:
        asset = _save_opinionated_cog(data, out_file, band)
    except ValueError:
        log.exception(
            "Failed to create COG, please check that you only have one timestep in the period."
        )
        exit(1)

    log.info(f"Finished writing: {asset.href}")


def create_rgb_cog(
    dc: Datacube,
    product: str,
    out_product: str,
    version: str,
    time: Tuple[str, str],
    time_str: str,
    s3_output_root: str,
    resolution: int,
    overwrite: bool,
):
    """Load red/green/blue and write the RGB visual COG."""
    log.info(f"Creating RGB COG for {product}/{version} over {time}")

    rgb_out_file = _get_path(s3_output_root, version, out_product, time_str, "tif", band="rgb")
    exists = s3_head_object(rgb_out_file) is not None
    if exists and not overwrite:
        log.info(f"RGB file exists, and overwrite is False. Not writing {rgb_out_file}")
        return pystac.Asset(media_type=pystac.MediaType.COG, href=rgb_out_file, roles=["visual"])

    start_local_dask()

    data: Dataset = dc.load(
        product=product,
        time=time,
        resolution=(-resolution, resolution),
        dask_chunks={"x": 2048, "y": 2048},
        measurements=["red", "green", "blue"],
    )

    # Just a count for information.
    datasets = list(dc.find_datasets(product=product, time=time))
    log.info(f"Found {len(datasets)} datasets for {product}/{version} over {time}")

    rgb_asset = _save_opinionated_cog(
        data[["red", "green", "blue"]],
        rgb_out_file,
        roles=["visual"],
    )
    log.info(f"Finished writing: {rgb_asset.href}")


def create_stac_item_for_mosaic(
    product: str,
    out_product: str,
    version: str,
    time: Tuple[str, str],
    time_str: str,
    bands: Tuple[str],
    s3_output_root: str,
    overwrite: bool,
):
    """Assemble and write the STAC item, referencing the band (and RGB) COGs that should already
    have been written to S3 by earlier steps. Does not re-load any pixel data."""
    out_stac_file = _get_path(s3_output_root, version, out_product, time_str, "stac-item.json")
    exists = s3_head_object(out_stac_file) is not None
    if exists and not overwrite:
        log.info(f"File exists, and overwrite is False. Not writing {out_stac_file}")
        return

    assets = {}
    for band in bands:
        out_file = _get_path(s3_output_root, version, out_product, time_str, "tif", band=band)
        assets[band] = pystac.Asset(media_type=pystac.MediaType.COG, href=out_file, roles=["data"])

    rgb_out_file = _get_path(s3_output_root, version, out_product, time_str, "tif", band="rgb")
    assets["rgb"] = pystac.Asset(media_type=pystac.MediaType.COG, href=rgb_out_file, roles=["visual"])

    item = create_stac_item(
        assets[bands[0]].href,
        id=f"{product}_{time_str}",
        assets=assets,
        with_proj=True,
        properties={
            "odc:product": out_product,
            "start_datetime": f"{time[0]}T00:00:00Z",
            "end_datetime": f"{time[1]}T23:59:59Z",
        },
    )
    item.set_self_href(out_stac_file)

    log.info(f"Writing STAC: {out_stac_file}")
    client = s3_client(aws_unsigned=False)
    s3_dump(
        data=json.dumps(item.to_dict(), indent=2),
        url=item.self_href,
        ACL="bucket-owner-full-control", # TODO: Is this needed?
        ContentType="application/json",
        s3=client,
    )


def _common_options(f):
    f = click.option("--product", type=str, default="s2_geomad_annual")(f)
    f = click.option("--out-product", type=str, default=None)(f)
    f = click.option("--version", type=str, default="1.0.0")(f)
    f = click.option("--time-start", type=str, default="2015")(f)
    f = click.option("--period", type=str, default="P1Y")(f)
    f = click.option("--resolution", type=int, default=120)(f)
    f = click.option("--s3-output-root", type=str, default="s3://piksel-staging-public-data/")(f)
    f = click.option("--overwrite", is_flag=True, default=False)(f)
    return f


@click.group()
def cli():
    """Create low-resolution mosaics (as per-band COGs, an RGB COG, and a STAC item) from a
    datacube product.

    This is split into three subcommands so that band creation can be fanned out in parallel:

        band  - create a COG for one band (run once per band, in parallel)
        rgb   - create the RGB visual COG (run once, after all bands)
        stac  - assemble and write the STAC item (run once, after rgb)

    Example:

        uv run src/low_res_mosaic/low_res_mosaic.py band \\
            --product s2_geomad_annual --time-start 2025 --period P1Y \\
            --band SMAD --resolution 120 \\
            --s3-output-root s3://piksel-staging-public-data/ --version 1.0.0

        uv run src/low_res_mosaic/low_res_mosaic.py rgb \\
            --product s2_geomad_annual --time-start 2025 --period P1Y \\
            --resolution 120 --s3-output-root s3://piksel-staging-public-data/ --version 1.0.0

        uv run src/low_res_mosaic/low_res_mosaic.py stac \\
            --product s2_geomad_annual --time-start 2025 --period P1Y \\
            --bands red,green,blue,rededge1,rededge2,rededge3,nir,nir08,swir16,swir22,BCMAD,EMAD,SMAD,COUNT \\
            --resolution 120 --s3-output-root s3://piksel-staging-public-data/ --version 1.0.0
    """
    pass


@cli.command("band")
@_common_options
@click.option("--band", type=str, required=True, help="The single band to create a COG for.")
def band_cmd(product, out_product, version, time_start, period, resolution, s3_output_root, overwrite, band):
    """Create a COG for a single band."""
    dc = Datacube()

    if not dc.index.products.get_by_name(product):
        log.exception(f"Product {product} not found")
        exit(1)

    time, time_str = _time_bounds(time_start, period)

    if out_product is None:
        out_product = f"{product}_{resolution}"

    create_band_cog(
        dc, product, out_product, version, time, time_str, band,
        s3_output_root.rstrip("/"), resolution, overwrite,
    )


@cli.command("rgb")
@_common_options
def rgb_cmd(product, out_product, version, time_start, period, resolution, s3_output_root, overwrite):
    """Create the RGB visual COG."""
    dc = Datacube()

    if not dc.index.products.get_by_name(product):
        log.exception(f"Product {product} not found")
        exit(1)

    time, time_str = _time_bounds(time_start, period)

    if out_product is None:
        out_product = f"{product}_{resolution}"

    create_rgb_cog(
        dc, product, out_product, version, time, time_str,
        s3_output_root.rstrip("/"), resolution, overwrite,
    )


@cli.command("stac")
@_common_options
@click.option("--bands", type=str, required=True, help="Comma separated list of bands included in the mosaic.", default="red,green,blue,rededge1,rededge2,rededge3,nir,nir08,swir16,swir22,BCMAD,EMAD,SMAD,COUNT")
def stac_cmd(product, out_product, version, time_start, period, resolution, s3_output_root, overwrite, bands):
    """Assemble and write the STAC item for a mosaic."""
    bands = bands.split(",")
    if not len(bands) > 0:
        log.exception("Please select at least one band")
        exit(1)

    time, time_str = _time_bounds(time_start, period)

    if out_product is None:
        out_product = f"{product}_{resolution}"

    create_stac_item_for_mosaic(
        product, out_product, version, time, time_str, bands,
        s3_output_root.rstrip("/"), overwrite
    )


if __name__ == "__main__":
    cli()