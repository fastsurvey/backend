import re

from cerberus import Validator, TypeDefinition


class ConfigurationValidator(Validator):

    TITLE_SCHEMA = {'type': 'string', 'maxlength': 100}
    DESCRIPTION_SCHEMA = {'type': 'string', 'maxlength': 1000}
    HINT_SCHEMA = TITLE_SCHEMA
    MANDATORY_SCHEMA = {'type': 'boolean'}

    EMAIL_FIELD_SCHEMA = {
        'type': 'dict',
        'schema': {
            'type': {'type': 'string', 'allowed': ['Email']},
            'title': TITLE_SCHEMA,
            'description': DESCRIPTION_SCHEMA,
            'regex': {'type': 'regex'},
            'hint': HINT_SCHEMA,
        },
    }
    OPTION_FIELD_SCHEMA = {
        'type': 'dict',
        'schema': {
            'type': {'type': 'string', 'allowed': ['Option']},
            'title': TITLE_SCHEMA,
            'description': DESCRIPTION_SCHEMA,
            'mandatory': MANDATORY_SCHEMA,
        },
    }
    RADIO_FIELD_SCHEMA = {
        'type': 'dict',
        'schema': {
            'type': {'type': 'string', 'allowed': ['Radio']},
            'title': TITLE_SCHEMA,
            'description': DESCRIPTION_SCHEMA,
            'fields': {'type': 'list', 'schema': OPTION_FIELD_SCHEMA},
        },
    }
    SELECTION_FIELD_SCHEMA = {
        'type': 'dict',
        'schema': {
            'type': {'type': 'string', 'allowed': ['Selection']},
            'title': TITLE_SCHEMA,
            'description': DESCRIPTION_SCHEMA,
            'min_select': {'type': 'integer', 'min': 0},
            'max_select': {'type': 'integer', 'min': 0},
            'fields': {'type': 'list', 'schema': OPTION_FIELD_SCHEMA},
        },
    }
    TEXT_FIELD_SCHEMA = {
        'type': 'dict',
        'schema': {
            'type': {'type': 'string', 'allowed': ['Text']},
            'title': TITLE_SCHEMA,
            'description': DESCRIPTION_SCHEMA,
            'min_chars': {'type': 'integer', 'min': 0, 'max': 10000},
            'max_chars': {'type': 'integer', 'min': 0, 'max': 10000},
        },
    }

    CONFIGURATION_SCHEMA = {
        'admin_name': {'type': 'string', 'minlength': 1, 'maxlength': 20},
        'survey_name': {'type': 'string', 'minlength': 1, 'maxlength': 20},
        'title': TITLE_SCHEMA,
        'description': DESCRIPTION_SCHEMA,
        'start': {'type': 'integer', 'min': 0},
        'end': {'type': 'integer', 'min': 0},
        'mode': {'type': 'integer', 'allowed': [0, 1, 2]},
        'fields': {
            'type': 'list',
            'schema': {
                'oneof': [
                    EMAIL_FIELD_SCHEMA,
                    OPTION_FIELD_SCHEMA,
                    RADIO_FIELD_SCHEMA,
                    SELECTION_FIELD_SCHEMA,
                    TEXT_FIELD_SCHEMA,
                ],
            },
        },
    }

    @classmethod
    def create(cls):
        """Factory method providing a simple interface to create a validator.

        A more elegant way to achieve this would be to override the __init__
        method of the Validator class. The __init__ method is somehow called
        multiple times, though, that's why using a factory method is the
        easier way.

        """
        return cls(cls.CONFIGURATION_SCHEMA, require_all=True)


    ### CUSTOM TYPE VALIDATIONS ###


    def _validate_type_regex(self, value):
        """Validate that a given value is a valid regular expression."""
        try:
            re.compile(value)
            return True
        except:
            return False


class SubmissionValidator(Validator):
    """The cerberus submission validator with added custom validation rules.

    For an explanation of the validation rules we kindly refer the curious
    reader to the FastSurvey and the cerberus documentations. They are omitted
    here to avoid documentation duplication and to keep the methods as
    overseeable as possible.

    """

    types_mapping = {
        'email': TypeDefinition('email', (str,), ()),
        'option': TypeDefinition('option', (bool,), ()),
        'text': TypeDefinition('text', (str,), ()),
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
            cls._generate_schema(configuration),
            require_all=True,
        )

    @staticmethod
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

    def _count_selections(self, value):
        """Count the number of selected options in a Selection field."""
        count = sum(value.values())
        return count


    ### CUSTOM TYPE VALIDATIONS ###


    def _validate_type_selection(self, value):
        """Validate the structure of a submission for the selection field."""
        if type(value) is not dict:
            return False
        for e in value.values():
            if type(e) is not bool:
                return False
        return True

    def _validate_type_radio(self, value):
        """Validate the structure of a submission for the radio field."""
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
