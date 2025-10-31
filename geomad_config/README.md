
# ODC-Stats Configuration Files

This folder contains the configuration files used to execute [`odc-stats`](https://github.com/opendatacube/odc-stats) processing tasks.

The `.yaml` files define configurable parameters for `odc-stats` runs and the parameters specified in a YAML configuration file will **override default values** used by `odc-stats`.


Example command to run an `odc-stats` job:

```bash
odc-stats run s2_l2a_2024--P1Y.db "2024--P1Y/235/-15" \
  --config gm_s2.yaml \
  --location file:///home/jovyan/dev/gm/ \
  --threads=8 \
  --memory-limit=30Gi
```

## References

- [ODC Stats Documentation](https://github.com/opendatacube/odc-stats)
- [DEAustralia Example Configs](https://github.com/GeoscienceAustralia/dea-config/tree/master/prod/services/odc-stats/geomedian)
