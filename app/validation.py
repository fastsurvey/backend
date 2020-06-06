from cerberus import Validator, TypeDefinition


class SubmissionValidator(Validator):
    """The cerberus submission validator with added custom validation rules.

    For an explanation of the validation rules we kindly refer the curious
    reader to the FastSurvey and the cerberus documentations. They are omitted 
    here to avoid documentation duplication and to keep the methods as 
    overseeable as possible.
    
    """

    types_mapping = Validator.types_mapping.copy()
    
    types_mapping['Selection'] = TypeDefinition('Selection', (dict,), ())
    types_mapping['List'] = TypeDefinition('List', (str,), ())
    types_mapping['Option'] = TypeDefinition('Option', (bool,), ())
    types_mapping['Text'] = TypeDefinition('Text', (str,), ())
    
    def _validate_min_chars(self, min_chars, field, value):
        """{'type': 'integer'}"""
        if len(value) < min_chars:
            self._error(field, f'Must be at least {min_chars} characters long') 
  
    def _validate_max_chars(self, max_chars, field, value):
        """{'type': 'integer'}"""
        if len(value) > max_chars:
            self._error(field, f'Must be at most {max_chars} characters long') 

    def _count_selections(self, value):
        """Count the number of selected options in a selection field."""
        count = 0
        for v in value.values():
            if isinstance(v, bool) and v:  # for option children
                count += 1
            if isinstance(v, str):  # for list children
                split = set([e.strip() for e in v.split(',') if e.strip()])
                count += len(split)
        return count

    def _validate_min_select(self, min_select, field, value):
        """{'type': 'integer'}"""
        if self._count_selections(value) < min_select:
            self._error(field, f'Must select at least {min_select} options')

    def _validate_max_select(self, max_select, field, value):
        """{'type': 'integer'}"""
        if self._count_selections(value) > max_select:
            self._error(field, f'Must select at most {max_select} options')


def _generate_schema(configuration):
    """Generate a cerberus validation schema from survey configuration."""

    def _generate_field_schema(field):
        """Recursively generate the cerberus schemas for a survey field."""
        fs = {'type': field['type']}
        if 'properties' in field.keys():
            if 'fields' in field['properties'].keys():
                fs['schema'] = {
                    str(i+1): _generate_field_schema(child)
                    for i, child
                    in enumerate(field['properties'].pop('fields'))
                }
            for k, v in field['properties'].items():
                fs[k] = v
        return fs

    schema = {
        'email': {
            'type': 'string',
            'regex': r'^[a-z]{2}[0-9]{2}[a-z]{3}@mytum\.de$',
        },
        'properties': {
            'type': 'dict',
            'schema': {
                str(i+1): _generate_field_schema(field)
                for i, field
                in enumerate(configuration['fields'])
            },
        },
    }
    return schema


def create_validator(configuration):
    """Create and return submission validator based on a survey configuration.

    This is not the most elegant way, but I cannot easily override the init 
    method of SubmissionValidator due to it being called several times. We use 
    this method in order to nonetheless provide abstraction when creating a 
    validator object.

    """
    return SubmissionValidator(
        _generate_schema(configuration), 
        require_all=True,
    )
