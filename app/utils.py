
def identify(configuration):
    """Build survey id from its configuration."""
    admin_name = configuration['admin_name']
    survey_name = configuration['survey_name']
    return f'{admin_name}.{survey_name}'
