# Test Structure

In order to keep tests as readable as possible and duplication to a minimum, much of the example data that is used in the tests is stored in JSON files:

The `data/surveys` directory contains valid example configurations, submissions, and results data, in exactly the format used in exchanges with the endpoints. The `aggregation_pipeline.json` is used for internal testing. Invalid examples of configurations and submissions are built dynamically from valid examples in `data.py`.

`data/account_datas.json` contains some valid test account datas, in exactly the format used in exchanges with the endpoints. Invalid examples of account datas are built dynamically from valid examples in `data.py`.
