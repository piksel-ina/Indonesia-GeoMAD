from collections.abc import Iterable, Sequence
from datacube.model import Dataset
from odc.geo.geobox import GeoBox
from odc.stats.plugins._registry import register, StatsPluginInterface
from odc.stats.io import load_with_native_transform
from eo_tides.eo import pixel_tides
import logging
import numpy as np
import xarray as xr
import dask.array as da
from odc.algo import (
    int_geomedian,
    enum_to_bool,
    mask_cleanup,
    erase_bad,
    keep_good_only,
)

"""
odc-stats plug-in for high and low tide composites
"""

_log = logging.getLogger(__name__)


def tidal_thresholds(
    tides_highres,
    threshold_lowtide=0.15,
    threshold_hightide=0.85,
    min_obs=0,
    time_dim="time",
):
    # Calculate per-pixel integer rankings for each tide height
    rank_n = tides_highres.rank(dim=time_dim)

    # Calculate pixel-based low and high ranking thresholds from
    # max ranking. Max ranking needs to be rounded up to the nearest
    # integer using "ceil" as xarray will give multiple observation
    # an average rank (e.g. 50.5) value if they are both identical.
    # Additionally: to ensure we capture all matching values, Low
    # threshold needs to be rounded up ("ceil"), and high tide
    # rounded down ("floor").
    rank_max = np.ceil(rank_n.max(dim=time_dim))
    rank_thresh_low = np.ceil(rank_max * threshold_lowtide)
    rank_thresh_high = np.floor(rank_max * threshold_hightide)

    # Update thresholds to ensure minimum number of valid observations
    if min_obs > 0:
        rank_thresh_low = np.maximum(rank_thresh_low, min_obs)
        rank_thresh_high = np.minimum(rank_thresh_high, rank_max - min_obs)

    # Calculate tide thresholds by masking tides by ranking threshold
    tide_thresh_low = tides_highres.where(rank_n <= rank_thresh_low).max(dim=time_dim)
    tide_thresh_high = tides_highres.where(rank_n >= rank_thresh_high).min(dim=time_dim)

    return tide_thresh_low, tide_thresh_high


def rename_add_prefix(ds, prefix, exclude_prefix="qa"):
    # Create a new dataset with renamed bands
    ds_renamed = ds.rename(
        {
            band: f"{prefix}_{band}"
            for band in ds.data_vars
            if not band.startswith(exclude_prefix)
        }
    )
    return ds_renamed


class HLTidalComposites(StatsPluginInterface):
    """
    Define a class to generate high- and low-tide S2 geomedian composites.
    """

    NAME = "tidal_composites"
    SHORT_NAME = NAME
    VERSION = "0.0.0"
    PRODUCT_FAMILY = "tidal_composites"

    def __init__(
        self,
        input_bands: tuple[str, ...],
        mask_band: str,
        tide_model: str,
        tide_model_dir: str,
        threshold_lowtide: float = 0.15,
        threshold_hightide: float = 0.85,
        min_obs: int = 0,
        eps: float = 1e-4,
        max_iters: int = 10000,
        nodata_classes: tuple[str, ...] | None = ("no data",),
        cloud_filters: dict[str | tuple[str, ...], Iterable[tuple[str, int]]] = None,
        group_by: str = "solar_day",
        **kwargs,
    ):
        cloud_filters = (
            {
                (
                    "cloud shadows",
                    "cloud medium probability",
                    "cloud high probability",
                    "thin cirrus",
                ): [("opening", 2), ("dilation", 5)],
            }
            if cloud_filters is None
            else cloud_filters
        )
        self.input_bands = input_bands
        self._mask_band = mask_band
        self._nodata_classes = nodata_classes
        self.cloud_filters = cloud_filters
        self.group_by = group_by
        self.tide_model = tide_model
        self.tide_model_dir = tide_model_dir
        self.threshold_lowtide = threshold_lowtide
        self.threshold_hightide = threshold_hightide
        self.min_obs = min_obs
        self.eps = eps
        self.max_iters = max_iters

        super().__init__(
            input_bands=tuple(input_bands) + (mask_band,),
            **kwargs,
        )

    @property
    def measurements(self) -> tuple[str, ...]:
        """
        Define the output bands by adding a suffix to the input bands and add the qa bands.
        """
        low_bands = [
            f"low_{band}" for band in self.input_bands if band != self._mask_band
        ]
        high_bands = [
            f"high_{band}" for band in self.input_bands if band != self._mask_band
        ]
        qa_bands = [
            "qa_count_clear_low",
            "qa_count_clear_high",
            "qa_count_clear_total",
            "qa_low_threshold",
            "qa_high_threshold",
        ]
        return low_bands + high_bands + qa_bands

    def native_transform(self, xx: xr.Dataset) -> xr.Dataset:
        """
        Define masking applied to the input data.
        """

        if self._mask_band not in xx.data_vars:
            return xx

        # Erase Data Pixels for which mask == nodata
        mask = xx[self._mask_band]
        bad = enum_to_bool(mask, self._nodata_classes)

        if self.cloud_filters is not None:
            for cloud_class, c_filter in self.cloud_filters.items():
                if not isinstance(cloud_class, tuple):
                    cloud_class = (cloud_class,)
                cloud_mask = enum_to_bool(mask, cloud_class)
                cloud_mask_buffered = mask_cleanup(cloud_mask, mask_filters=c_filter)
                bad = cloud_mask_buffered | bad
        else:
            cloud_shadow_mask = enum_to_bool(mask, ("cloud", "shadow"))
            bad = cloud_shadow_mask | bad
            _log.info("Applying cloud/shadow mask without buffering.")

        xx = xx.drop_vars([self._mask_band])
        xx = erase_bad(xx, bad)
        xx["bad"] = bad

        return xx

    def reduce(self, xx: xr.Dataset) -> xr.Dataset:
        """
        Define the calculation applied to the input data.
        """
        _log.info("Modelling tide heights for each pixel")
        tides_highres = pixel_tides(
            data=xx,
            time=xx["time"],
            model=self.tide_model,
            resample=True,
            directory=self.tide_model_dir,
        )
        _log.info("Masking tides")
        tides_highres = erase_bad(tides_highres, xx["bad"], nodata=np.nan)

        _log.info(
            f"Calculating low and high tide thresholds with minimum {self.min_obs} observations"
        )
        # Create masks for selecting satellite observations below and above the
        # low and high tide thresholds
        low_threshold, high_threshold = tidal_thresholds(
            tides_highres=tides_highres,
            threshold_lowtide=self.threshold_lowtide,
            threshold_hightide=self.threshold_hightide,
            min_obs=self.min_obs,
        )
        low_mask = tides_highres <= low_threshold
        high_mask = tides_highres >= high_threshold

        # Keep only scenes with at least 1% valid data to speed up geomedian
        low_keep = low_mask.mean(dim=["x", "y"]) >= 0.01
        high_keep = high_mask.mean(dim=["x", "y"]) >= 0.01
        ds_low = xx.sel(spec=low_keep.values).chunk({"spec": -1})
        ds_high = xx.sel(spec=high_keep.values).chunk({"spec": -1})

        low_mask = low_mask.sel(time=low_keep).chunk(
            {("time" if k == "spec" else k): v for k, v in ds_low.chunksizes.items()}
        )
        high_mask = high_mask.sel(time=high_keep).chunk(
            {("time" if k == "spec" else k): v for k, v in ds_high.chunksizes.items()}
        )
        # Use `keep_good_only` to set any pixels outside of the tide masks to nodata
        ds_low_masked = keep_good_only(x=ds_low, where=low_mask)
        ds_high_masked = keep_good_only(x=ds_high, where=high_mask)

        _log.info("Calculating clear counts")
        qa_count_clear_low = (~ds_low_masked.bad).sum(dim="spec").astype("int16")
        qa_count_clear_high = (~ds_high_masked.bad).sum(dim="spec").astype("int16")
        qa_count_clear_total = (~xx.bad).sum(dim="spec").astype("int16")

        ds_low_masked = ds_low_masked.drop_vars(["bad"])
        ds_high_masked = ds_high_masked.drop_vars(["bad"])

        # Calculate low and high tide geomedians
        _log.info(f"Generating low tide geomedian from {len(ds_low_masked.spec)} images")
        ds_lowtide = int_geomedian(
            ds=ds_low_masked,
            maxiters=self.max_iters,
            eps=self.eps,
        )
        _log.info(f"Generating high tide geomedian from {len(ds_high_masked.spec)} images")
        ds_hightide = int_geomedian(
            ds=ds_high_masked,
            maxiters=self.max_iters,
            eps=self.eps,
        )

        # Rename low and high tide bands to add "low"/"high"
        ds_hightide = rename_add_prefix(ds_hightide, "high")
        ds_lowtide = rename_add_prefix(ds_lowtide, "low")

        # Concatenate into a single output dataset
        ds_composites = xr.merge([ds_lowtide, ds_hightide], compat="no_conflicts")

        ds_composites["qa_count_clear_low"] = qa_count_clear_low
        # low and high tide clear counts are similar but not identical?
        ds_composites["qa_count_clear_high"] = qa_count_clear_high
        # Add the total count clear (Only add once)
        ds_composites["qa_count_clear_total"] = qa_count_clear_total

        # Add low and high tide thresholds to the output datasets
        ds_composites["qa_low_threshold"] = low_threshold
        ds_composites["qa_high_threshold"] = high_threshold

        return ds_composites


register("hltc", HLTidalComposites)
