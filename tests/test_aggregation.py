import app.aggregation as aggregation


def test_building_aggregation_pipeline(
        username,
        configurationss,
        aggregation_pipelines,
    ):
    """Test that correct aggregation pipeline is built from configuration."""
    for survey_name, configurations in configurationss.items():
        configuration = {
            'username': username,
            **configurations['valid'],
        }
        x = aggregation.build_aggregation_pipeline(configuration)
        assert x == aggregation_pipelines[survey_name]
