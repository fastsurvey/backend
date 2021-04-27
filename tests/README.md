# Test Structure

In order to keep tests as readable as possible and duplication to a minimum, much of the example data that is used in the tests is stored in JSON files:

The `data/surveys` directory contains configuration, submission, validation and results data for some test surveys. The `configurations.json` and `submissions.json` files contain both valid and invalid entries, which are used and checked while testing. The JSON format of the (valid) entries in `configurations.json`, `submissions.json` and `results.json` is exactly the format used in exchanges with the endpoints. `schema.json` contains the dynamically generated cerberus submission validation schema that is only used internally.

`data/accounts.json` contains some valid and invalid test accounts. The first valid entry is used for every test that is tied to a specific user, the rest are only for validation purposes.

The `data/variables.json` file contains some miscellaneous test values that are used in multiple places.
