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

## Manage Development Environment
### Environment Setup with UV

1. **Install System Dependencies**  

   Install PostgreSQL development libraries required by some Python packages:
    
    ```bash
    sudo apt-get update
    sudo apt-get install libpq-dev python3-dev
    ```

3. **Install Project Dependencies**  

   Create virtual environment and install all packages from `pyproject.toml`:
    
    ```bash
    uv sync
    ```

4. **Activate Virtual Environment**

    Activate the environment to access installed packages:
    
    ```bash
    source .venv/bin/activate
    ```

5. **Register Jupyter Kernel**

    Make the environment available in Jupyter notebooks:
    
    ```bash
    python -m ipykernel install --user --name indonesia-geomad --display-name "Indonesia GeoMAD"
    ```

### Select Kernel in Notebook

1. Open your notebook (`.ipynb` file)
2. Click **Kernel** → **Change Kernel** → **Indonesia GeoMAD**
3. Verify the kernel name appears in the top-right corner

### Add New Dependencies

If you need to install additional packages:

```bash
# Activate environment first
source .venv/bin/activate

# Add a new package
uv add package-name

# Example: Add a specific package
uv add numpy
```

## Acknowledgments

- [Open Data Cube](https://www.opendatacube.org/) community
- [odc-stats](https://github.com/opendatacube/odc-stats) developers
- [Digital Earth Australia](https://www.dea.ga.gov.au/) for GeoMAD algorithm development
