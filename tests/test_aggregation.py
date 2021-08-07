import app.aggregation as aggregation


def test_building_aggregation_pipeline(
        username,
        configurations,
        aggregation_pipelines,
    ):
    """Test that correct aggregation pipeline is built from configuration."""
    for survey_name, configuration in configurations.items():
        configuration = {'username': username, **configuration}
        x = aggregation._build_aggregation_pipeline(configuration)
        assert x == aggregation_pipelines[survey_name]


def test_building_default_results(configurations, default_resultss):
    """Test that results are correct for complex survey with no submissions."""
    for survey_name, configuration in  configurations.items():
        x = aggregation._build_default_results(configuration)
        assert x == default_resultss[survey_name]
