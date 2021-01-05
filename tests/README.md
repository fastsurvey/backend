## Test Structure

The `surveys` folder contains a subfolder for each test survey, each containing a `configuration.json`, `submission.json`, `results.json` and a `schema.json` file. The JSON format of `configuration.json` and `results.json` and the JSON format of the valid submissions in `submissions.json` is exactly the format used in exchanges with the endpoints. `schema.json` contains the cerberus submission validation schema that is only used internally.

The `parameters.json` file contains some general test values that are used in multiple places.
