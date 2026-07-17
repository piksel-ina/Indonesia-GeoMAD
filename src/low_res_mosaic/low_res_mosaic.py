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
    dataset: Dataset, out_file: str, band: str | None = None,
) -> Asset:
    data_array: DataArray
    if band is not None:
        data_array = dataset[band].squeeze("time")
    else:
        data_array = dataset.squeeze("time").to_stacked_array("bands", ["x", "y"])

    cog = save_cog_with_dask(
        data_array,
        out_file,
        # TODO: Tune compression:
        # compression="zstd" # See if this is smaller than deflate (default)
        # level=15, # zstd level, higher = smaller/slower; tune to taste
        # predictor=2,   # horizontal differencing for integer bands — improves DEFLATE/ZSTD ratio on smooth reflectance data with no downside
        blocksize=1024,
        overview_resampling="average",
        bigtiff=True,
        # SPARSE_OK=True,
        stats=True,
    )

    cog.compute()

    return pystac.Asset(media_type=pystac.MediaType.COG, href=out_file, roles=["data"])


def _get_path(s3_output_root, version: str, out_product, time_str, ext, band=None):
    base = f"{s3_output_root}/{out_product}/{version}/{time_str}/{out_product}_{time_str}"
    if band is None:
        return f"{base}.{ext}"
    else:
        return f"{base}_{band}.{ext}"


def create_low_res_mosaic(
    dc: Datacube,
    product: str,
    out_product: str,
    version: str,
    time: Tuple[str, str],
    time_str: str,
    bands: Tuple[str],
    s3_output_root: str,
    split_bands: bool,
    resolution: int,
    overwrite: bool,
):
    log.info(f"Creating mosaic for {product}/{version} over {time}")

    client = start_local_dask()

    assets = {}
    data: Dataset = dc.load(
        product=product,
        time=time,
        resolution=(-resolution, resolution),
        dask_chunks={"x": 2048, "y": 2048},
        measurements=bands,
    )

    datasets = list(dc.find_datasets(product=product, time=time))
    log.info(f"Found {len(datasets)} datasets for {product}/{version} over {time}")


    if not split_bands:
        log.info("Creating a single tif file")
        out_file = _get_path(s3_output_root, version, out_product, time_str, "tif")
        exists = s3_head_object(out_file) is not None # TODO: Do this check earlier (before loading data).
        skip_writing = not (not exists or overwrite)
        if not skip_writing:
            log.info(f"File doesn't exist, or overwrite is True. Writing {out_file}")
            try:
                asset = _save_opinionated_cog(
                    data,
                    out_file,
                )
            except ValueError:
                log.exception(
                    "Failed to create COG, please check that you only have one timestep in the period."
                )
                exit(1)
            log.info(f"Finished writing: {asset.href}")
        else:
            log.info(f"File exists, and overwrite is False. Not writing {out_file}")
            asset = pystac.Asset(media_type=pystac.MediaType.COG, href=out_file, roles=["data"])
        
        assets[bands[0]] = asset

    else:
        log.info(f"Creating multiple tif files (one per band for bands: {bands})")

        for band in bands:
            out_file = _get_path(
                s3_output_root, version, out_product, time_str, "tif", band=band
            )
            exists = s3_head_object(out_file) is not None
            skip_writing = not (not exists or overwrite)
            if not skip_writing:
                log.info(f"File doesn't exist, or overwrite is True. Writing {out_file}")
                try:
                    asset = _save_opinionated_cog(
                        data,
                        out_file,
                        band,
                    )
                    log.info(f"Finished writing: {asset.href}")
                except ValueError:
                    log.exception(
                        "Failed to create COG, please check that you only have one timestep in the period."
                    )
                    exit(1)

                # Aggressively heavy handed, but we get memory leaks otherwise
                client.restart() # TODO: Don't do this on the last iteration. It is not needed.
            else:
                log.info(f"File exists, and overwrite is False. Not writing {out_file}")
                # Still describe it in the STAC item — it exists, just wasn't (re)written this run
                asset = pystac.Asset(media_type=pystac.MediaType.COG, href=out_file, roles=["data"])

            assets[band] = asset

    out_stac_file = _get_path(s3_output_root, version, out_product, time_str, "stac-item.json")
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
        ACL="bucket-owner-full-control",
        ContentType="application/json",
        s3=client,
    )


@click.command("create-mosaic")
@click.option("--product", type=str, default="s2_geomad_annual")
@click.option("--out-product", type=str, default=None)
@click.option("--version", type=str, default="1.0.0")
@click.option("--time-start", type=str, default="2015")
@click.option("--period", type=str, default="P1Y")
@click.option("--bands", type=str, default="red,green,blue")
@click.option("--resolution", type=int, default=1000)
@click.option(
    "--s3-output-root",
    type=str,
    default="s3://piksel-staging-public-data/",
)
@click.option("--split-bands", is_flag=True, default=True)
@click.option("--overwrite", is_flag=True, default=False)
def cli(
    product,
    out_product,
    version,
    time_start,
    period,
    bands,
    resolution,
    s3_output_root,
    split_bands,
    overwrite,
):
    """
    Create a mosaic of a given product and time period including a STAC item.

    If --split-bands is set, the bands will be split into separate files, and the name will have the band
    name appended to the end.

    An example command is:

        uv run src/low_res_mosaic/low_res_mosaic.py \
            --product s2_geomad_annual \
            --time-start 2021 \
            --period P1Y \
            --bands red,green,blue \
            --resolution 1000 \
            --s3-output-root s3://piksel-staging-public-data/ \
            --split-bands \
            --version 1.0.0
    """
    dc = Datacube()

    bands = bands.split(",")
    if not len(bands) > 0:
        log.exception("Please select at least one band")
        exit(1)

    if not dc.index.products.get_by_name(product):
        log.exception(f"Product {product} not found")
        exit(1)

    if period not in ["P1Y", "P6M"]:
        log.exception(f"Time period {period} not supported, please use one of P1Y or P6M")
        exit(1)

    time_str = f"{time_start}--{period}"
    if period == "P1Y":
        time = (f"{time_start}-01-01", f"{time_start}-12-31")
    elif period == "P6M":
        year, start_month = [int(s) for s in time_start.split("-")]
        end_month = start_month + 5
        end_month_n_days = monthrange(year, end_month)[1]

        time = (
            f"{year}-{start_month:02d}-01",
            f"{year}-{end_month:02d}-{end_month_n_days}",
        )

    if out_product is None:
        out_product = f"{product}_{resolution}"

    create_low_res_mosaic(
        dc,
        product,
        out_product,
        version,
        time,
        time_str,
        bands,
        s3_output_root.rstrip("/"),
        split_bands,
        resolution,
        overwrite,
    )

if __name__ == "__main__":
    cli()