import app.aggregation as aggregation


def test_building_aggregation_pipeline(
        username,
        configuration,
        aggregation_pipeline,
    ):
    """Test that correct aggregation pipeline is built from configuration."""
    x = aggregation._build_aggregation_pipeline(configuration)
    assert x == aggregation_pipeline
