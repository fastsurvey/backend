from cerberus import Validator, TypeDefinition


class ConfigurationValidator(Validator):

    @classmethod
    def create(cls):

        schema = {
            'admin_name': {'type': 'string', 'minlength': 1, 'maxlength': 20},
            'survey_name': {'type': 'string', 'minlength': 1, 'maxlength': 20},
            'title': {'type': 'string', 'maxlength': 100},
            'description': {'type': 'string', 'maxlength': 1000},
            'start': {'type': 'integer', 'min': 0},
            'end': {'type': 'integer', 'min': 0},
            'mode': {'type': 'integer', 'allowed': [0, 1, 2]},
            'fields': {'type': 'dict'},
        }

        return cls(schema, require_all=True)


class SubmissionValidator(Validator):
    """The cerberus submission validator with added custom validation rules.

    For an explanation of the validation rules we kindly refer the curious
    reader to the FastSurvey and the cerberus documentations. They are omitted
    here to avoid documentation duplication and to keep the methods as
    overseeable as possible.

    """

    types_mapping = {
        'Email': TypeDefinition('Email', (str,), ()),
        'Option': TypeDefinition('Option', (bool,), ()),
        'Text': TypeDefinition('Text', (str,), ()),
    }

    @classmethod
    def create(cls, configuration):
        """Factory method providing a simple interface to create a validator.

        A more elegant way to achieve this would be to override the __init__
        method of the Validator class. The __init__ method is somehow called
        multiple times, though, that's why using a factory method is the
        easier way.

        """
        return cls(
            _generate_schema(configuration),
            require_all=True,
        )

    def _count_selections(self, value):
        """Count the number of selected options in a Selection field."""
        count = sum(value.values())
        return count


    ### CUSTOM TYPE VALIDATIONS ###


    def _validate_type_Selection(self, value):
        """Validate the structure of a submission for the Selection field."""
        if type(value) is not dict:
            return False
        for e in value.values():
            if type(e) is not bool:
                return False
        return True

    def _validate_type_Radio(self, value):
        """Validate the structure of a submission for the Radio field."""
        if not self._validate_type_Selection(value):
            return False
        if self._count_selections(value) != 1:
            return False
        return True


    ### CUSTOM VALIDATION RULES ###


    def _validate_min_chars(self, min_chars, field, value):
        """{'type': 'integer'}"""
        if len(value) < min_chars:
            self._error(field, f'Must be at least {min_chars} characters long')

    def _validate_max_chars(self, max_chars, field, value):
        """{'type': 'integer'}"""
        if len(value) > max_chars:
            self._error(field, f'Must be at most {max_chars} characters long')

    def _validate_min_select(self, min_select, field, value):
        """{'type': 'integer'}"""
        if self._count_selections(value) < min_select:
            self._error(field, f'Must select at least {min_select} options')

    def _validate_max_select(self, max_select, field, value):
        """{'type': 'integer'}"""
        if self._count_selections(value) > max_select:
            self._error(field, f'Must select at most {max_select} options')

    def _validate_mandatory(self, mandatory, field, value):
        """{'type': 'boolean'}"""
        if mandatory:
            if (
                type(value) is bool and not value
                or type(value) is str and value == ''
            ):
                self._error(field, f'This field is mandatory')


def _generate_schema(configuration):
    """Generate the cerberus validation schema from a survey configuration."""

    rules = [
        'min_chars',
        'max_chars',
        'min_select',
        'max_select',
        'mandatory',
        'regex',
    ]

    def _generate_field_schema(field):
        """Recursively generate the cerberus schemas for a survey field."""
        fs = {'type': field['type']}
        if 'fields' in field.keys():
            fs['schema'] = {
                str(i+1): _generate_field_schema(subfield)
                for i, subfield
                in enumerate(field['fields'])
            }
        for rule, value in field.items():
            if rule in rules:
                fs[rule] = value
        return fs

    schema = {
        str(i+1): _generate_field_schema(field)
        for i, field
        in enumerate(configuration['fields'])
    }
    return schema
