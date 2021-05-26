import re
import cerberus
import functools

import app.utils as utils


# string validation regexes
_REGEXES = {
    'username': r'^[a-z0-9-]{2,20}$',
    'email_address': r'^.+@.+$',
    'survey_name': r'^[a-z0-9-]{2,20}$',
}

# maximum character lengths (inclusive)
_LENGTHS = {
    'S': 128,
    'M': 1024,
    'L': 4096,
}


################################################################################
# Account Validation
################################################################################


class AccountValidator(cerberus.Validator):
    """The custom cerberus validator for validating user account data.

    We could use pydantic to validate the account data instead, as the data
    model is static and relatively easy. We do it with cerberus though in
    order to validate everything similarly and because we can test better
    using cerberus.

    """

    _SCHEMA = {
        'username': {'type': 'string', 'regex': _REGEXES['username']},
        'password': {'type': 'string', 'minlength': 8, 'maxlength': 64},
        'email_address': {
            'type': 'string',
            'maxlength': _LENGTHS['M'],
            'regex': _REGEXES['email_address'],
        },
    }

    def __init__(self, *args, **kwargs):
        """Initialize with predefined account validation schema."""
        super(AccountValidator, self).__init__(
            self._SCHEMA,
            *args,
            require_all=True,
            **kwargs,
        )


################################################################################
# Configuration Validation
################################################################################


class ConfigurationValidator():

    _FIELD_KEYS = {
        'configuration': {
            'survey_name',
            'title',
            'description',
            'start',
            'end',
            'draft',
            'authentication',
            'limit',
            'fields',
        },
        'email': {'type', 'title', 'description', 'regex', 'hint'},
        'option': {'type', 'title', 'description', 'required'},
        'radio': {'type', 'title', 'description', 'fields'},
        'selection': {
            'type',
            'title',
            'description',
            'min_select',
            'max_select',
            'fields',
        },
        'text': {'type', 'title', 'description', 'min_chars', 'max_chars'},
    }

    def validate(self, value):
        """Validate that the argument is a valid survey configuration."""
        return (
            type(value) is dict
            and set(value.keys()) == self._FIELD_KEYS['configuration']
            and type(value['survey_name']) is str
            and re.match(_REGEXES['survey_name'], value['survey_name'])
            and type(value['title']) is str
            and 1 <= len(value['title']) <= _LENGTHS['S']
            and type(value['description']) is str
            and len(value['description']) <= _LENGTHS['L']
            and type(value['start']) is type(value['end']) is int
            and 0 <= value['start'] <= value['end'] <= 4102444800
            and type(value['draft']) is bool
            and value['authentication'] in ['open', 'email']
            and type(value['limit']) is int
            and 0 <= value['limit'] <= 100
            and type(value['fields']) is list
            and 1 <= len(value['fields']) <= _LENGTHS['S']
            and all([
                (
                    self._validate_email(field)
                    or self._validate_option(field)
                    or self._validate_radio(field)
                    or self._validate_selection(field)
                    or self._validate_text(field)
                )
                for field
                in value['fields']
            ])
            and sum([
                self._validate_email(field)
                for field
                in value['fields']
            ]) == int(value['authentication'] == 'email')
        )

    def _base_validate(func):
        @functools.wraps(func)
        def wrapper(self, value):
            return (
                type(value) is dict
                and 'type' in value.keys()
                and value['type'] in self._FIELD_KEYS.keys()
                and set(value.keys()) == self._FIELD_KEYS[value['type']]
                and type(value['title']) == str
                and 1 <= len(value['title']) <= _LENGTHS['S']
                and type(value['description']) is str
                and len(value['description']) <= _LENGTHS['L']
                and func(self, value)
            )
        return wrapper

    @_base_validate
    def _validate_email(self, value):
        """Validate that the argument is a valid email field."""
        return (
            value['type'] == 'email'
            and type(value['regex']) is str
            and len(value['regex']) <= _LENGTHS['M']
            and utils.isregex(value['regex'])
            and type(value['hint']) is str
            and len(value['hint']) <= _LENGTHS['S']
        )

    @_base_validate
    def _validate_option(self, value):
        """Validate that the argument is a valid option field."""
        return (
            value['type'] == 'option'
            and type(value['required']) is bool
        )

    @_base_validate
    def _validate_radio(self, value):
        """Validate that the argument is a valid radio field."""
        return (
            value['type'] == 'radio'
            and type(value['fields']) is list
            and 2 <= len(value['fields']) <= _LENGTHS['S']
            and all([
                self._validate_option(field)
                for field
                in value['fields']
            ])
        )

    @_base_validate
    def _validate_selection(self, value):
        """Validate that the argument is a valid selection field."""
        return (
            value['type'] == 'selection'
            and type(value['fields']) is list
            and 2 <= len(value['fields']) <= _LENGTHS['S']
            and all([
                self._validate_option(field)
                for field
                in value['fields']
            ])
            and type(value['min_select']) is type(value['max_select']) is int
            and 0 <= value['min_select'] <= value['max_select']
            and value['max_select'] <= len(value['fields'])
        )

    @_base_validate
    def _validate_text(self, value):
        """Validate that the argument is a valid text field."""
        return (
            value['type'] == 'text'
            and type(value['min_chars']) is type(value['max_chars']) is int
            and 0 <= value['min_chars'] <= value['max_chars']
            and value['max_chars'] <= _LENGTHS['L']
        )


################################################################################
# Submission Validation
################################################################################


class SubmissionValidator(cerberus.Validator):
    """The cerberus submission validator with added custom validation rules.

    For an explanation of the validation rules we kindly refer the curious
    reader to the FastSurvey and the cerberus documentations. They are omitted
    here to avoid documentation duplication and to keep the methods as
    overseeable as possible.

    """

    types_mapping = {
        'option': cerberus.TypeDefinition('option', (bool,), ()),
        'text': cerberus.TypeDefinition('text', (str,), ()),
    }

    @classmethod
    def create(cls, configuration):
        """Factory method to initialize with dynamically generated schema.

        A more elegant way to achieve this would be to override the __init__
        method of the Validator class. Contrary to the other validators, I
        didn't get this to work here, somehow connected to the additional
        function parameter that was needed.

        """
        return cls(
            cls._generate_validation_schema(configuration),
            require_all=True,
        )

    @staticmethod
    def _generate_validation_schema(configuration):
        """Generate cerberus validation schema from a survey configuration.

        The rules dict specifies as keys all validation rule names there are.
        We map the validation rule names to the dict values while generating
        the schema in order to avoid collisions with cerberus' predefined
        rules as e.g. the case with 'required'.

        """

        rules = {
            'min_chars': 'min_chars',
            'max_chars': 'max_chars',
            'min_select': 'min_select',
            'max_select': 'max_select',
            'required': 'req',
            'regex': 'regex',
        }

        def _generate_field_schema(field):
            """Recursively generate the cerberus schemas for a survey field."""
            schema = {'type': field['type']}
            if 'fields' in field.keys():
                schema['schema'] = {
                    str(i+1): _generate_field_schema(subfield)
                    for i, subfield
                    in enumerate(field['fields'])
                }
            for rule, value in field.items():
                if rule in rules.keys():
                    schema[rules[rule]] = value
            return schema

        schema = {
            str(i+1): _generate_field_schema(field)
            for i, field
            in enumerate(configuration['fields'])
        }
        return schema

    def _count_selections(self, value):
        """Count the number of selected options in a selection field."""
        count = sum(value.values())
        return count


    ### CUSTOM TYPE VALIDATIONS ###


    def _validate_type_email(self, value):
        """Validate the structure of a submission for the email field."""
        return (
            type(value) is str
            and len(value) <= 1024
            and re.match(_REGEXES['email_address'], value)
        )

    def _validate_type_selection(self, value):
        """Validate the structure of a submission for the selection field."""
        return (
            type(value) is dict
            and all([type(e) is bool for e in value.values()])
        )

    def _validate_type_radio(self, value):
        """Validate the structure of a submission for the radio field."""
        return (
            self._validate_type_selection(value)
            and self._count_selections(value) == 1
        )


    ### CUSTOM VALIDATION RULES ###


    def _validate_min_chars(self, min_chars, field, value):
        """{'type': 'integer'}"""
        if type(value) is not str or len(value) < min_chars:
            self._error(field, f'must be at least {min_chars} characters long')

    def _validate_max_chars(self, max_chars, field, value):
        """{'type': 'integer'}"""
        if type(value) is not str or len(value) > max_chars:
            self._error(field, f'must be at most {max_chars} characters long')

    def _validate_min_select(self, min_select, field, value):
        """{'type': 'integer'}"""
        if self._count_selections(value) < min_select:
            self._error(field, f'must select at least {min_select} options')

    def _validate_max_select(self, max_select, field, value):
        """{'type': 'integer'}"""
        if self._count_selections(value) > max_select:
            self._error(field, f'must select at most {max_select} options')

    def _validate_req(self, req, field, value):
        """{'type': 'boolean'}"""
        if (
            req
            and not (type(value) is bool and value)
            and not (type(value) is str and value != '')
        ):
            self._error(field, f'this field is required')
