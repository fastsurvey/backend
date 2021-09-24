import app.aggregation as aggregation


def test_building_aggregation_pipeline(
        username,
        configurations,
        aggregation_pipelines,
    ):
    """Test that correct aggregation pipeline is built from configuration."""
    for survey_name, configuration in configurations.items():
        x = aggregation._build_aggregation_pipeline(configuration)
        assert x == aggregation_pipelines[survey_name]
