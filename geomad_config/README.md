
# ODC-Stats Configuration Files

A [`odc-stats`](https://github.com/opendatacube/odc-stats) workflow consists of two steps.

First is the creation of a database file, e.g. by running the following command:

```bash
odc-stats save-tasks --frequency annual \
  --grid 'ESRI:54034;10;5000' --year 2024 \
  --input-products s2_l2a
```

The database file created by the `save-tasks` step and a tile identifer can be used in the following example command to run an `odc-stats` job:

```bash
odc-stats run s2_l2a_2024--P1Y.db "2024--P1Y/235/-15" \
  --config gm_s2.yaml \
  --location file:///home/jovyan/dev/gm/ \
  --threads=8 \
  --memory-limit=30Gi
```

This folder contains the configuration files used to in the `run` step to execute  processing tasks.

The `.yaml` files define configurable parameters for `odc-stats` runs and the parameters specified in a YAML configuration file will **override default values** used by `odc-stats`.


## References

- [ODC Stats Documentation](https://github.com/opendatacube/odc-stats)
- [A Notebook Explanation of odc-stats Plugin](https://nbviewer.org/urls/raw.githack.com/opendatacube/odc-stats/develop/docs/odc-stats-explained.ipynb)
- [DEAustralia Example Configs](https://github.com/GeoscienceAustralia/dea-config/tree/master/prod/services/odc-stats/geomedian)
