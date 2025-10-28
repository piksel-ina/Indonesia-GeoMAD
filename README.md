# Indonesia-GeoMAD

Configuration files and workflows for generating GeoMAD (Geometric Median Absolute Deviation) statistics over Indonesia using [odc-stats](https://github.com/opendatacube/odc-stats) and Argo Workflows.

## Overview

This repository contains:
- **ODC-stats configuration files** for GeoMAD statistics processing
- **Argo Workflow definitions** for orchestrating large-scale processing
- **Testing scripts** for validation and quality control
- **Deployment templates** and utilities

## GeoMAD Statistics

This repository supports generation of multiple spectral statistics:

- **Geomedian** - Geometric median composite (multi-dimensional median)
- **MAD** - Median Absolute Deviation (measure of spectral variability)
- **SMAD** - Standardized MAD (normalized deviation)
- **EMAD** - Euclidean MAD (distance-based deviation)
- **BCMAD** - Bray-Curtis MAD (compositional deviation)
- **Count** - Valid observation counts
- **Percentiles** - Spectral percentile statistics

## Acknowledgments

- [Open Data Cube](https://www.opendatacube.org/) community
- [odc-stats](https://github.com/opendatacube/odc-stats) developers
- [Digital Earth Australia](https://www.dea.ga.gov.au/) for GeoMAD algorithm development
