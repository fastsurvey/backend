import re

from cerberus import Validator, TypeDefinition
from enum import Enum

from app.utils import isregex


# string validation regexes
REGEXES = {
    'username': r'^[a-z0-9-]{2,20}$',
    'email_address': r'^.+@.+\..+$',
    'survey_name': r'^[a-z0-9-]{2,20}$',
}

# maximum character lengths (inclusive)
LENGTHS = {
    'S': 128,
    'M': 1024,
    'L': 4096,
}


################################################################################
# Account Validation
################################################################################


class AccountValidator(Validator):
    """The custom cerberus validator for validating user account data.

    We could use pydantic to validate the account data instead, as the data
    model is static and relatively easy. We do it with cerberus though in
    order to validate everything similarly and because we can test better
    using cerberus.

    """

    SCHEMA = {
        'username': {
            'type': 'string',
            'regex': REGEXES['username'],
        },
        'email_address': {
            'type': 'string',
            'maxlength': LENGTHS['M'],
            'regex': REGEXES['email_address'],
        },
        'password': {
            'type': 'string',
            'minlength': 8,
            'maxlength': 64,
        },
    }

    def __init__(self, *args, **kwargs):
        """Initialize with predefined account validation schema."""
        super(AccountValidator, self).__init__(
            self.SCHEMA,
            *args,
            require_all=True,
            **kwargs,
        )


################################################################################
# Configuration Validation
################################################################################


'''

class ConfigurationValidatorNew():

    def validate(self, value):
        """Validate the field title and description."""
        return (
            type(value['title']) == str
            and len(value['title']) <= LENGTHS['S']
            and type(value['description']) == str
            and len(value['description']) <= LENGTHS['L']
        )

'''


class ConfigurationValidator(Validator):
    """The custom cerberus validator for validating survey configurations."""

    def __init__(self, *args, **kwargs):
        """Initialize with predefined configuration validation schema."""
        super(ConfigurationValidator, self).__init__(
            {'__root__': {'type': 'configuration'}},
            *args,
            require_all=True,
            **kwargs,
        )

    def validate(self, document, schema=None, update=False, normalize=True):
        """Overridden validate method used to type-check the root dict.

        It seems to be impossible in cerberus to validate a field depending
        on the value of another field. For example, for a survey we want to
        have the value of `end` to be greater or equal to `start`. I did not
        find a possibility to do this other than writing custom type classes
        and thus checking the field values with simple comparisons instead
        of cerberus' schemas. The downside of this is that the error messages
        are now no longer informative. As we also need to cross-check `start`
        and `end` which are not nested, we need to implement type checking
        the entire document as this is not possible out of the box. I adapted
        the solution from https://stackoverflow.com/questions/49762642. If
        someone knows of a better alternative, please let me know.

        """
        result = super(ConfigurationValidator, self).validate(
            {'__root__': document},
            schema,
            update,
            normalize,
        )
        self.document = self.document['__root__']
        return result


    ### CUSTOM TYPE VALIDATIONS ###


    def _validate_type_configuration(self, value):
        """Validate that value is a correct survey configuration"""
        keys = {
            'survey_name',
            'title',
            'description',
            'start',
            'end',
            'draft',
            'authentication',
            'limit',
            'fields',
        }
        return (
            type(value) is dict
            and set(value.keys()) == keys
            and type(value['survey_name']) == str
            and re.match(REGEXES['survey_name'], value['survey_name'])
            and type(value['title']) == str
            and 1 <= len(value['title']) <= LENGTHS['S']
            and type(value['description']) == str
            and len(value['description']) <= LENGTHS['L']
            and type(value['start']) == type(value['end']) == int
            and 0 <= value['start'] <= value['end'] <= 4102444800
            and type(value['draft']) == bool
            and value['authentication'] in ['open', 'email']
            and type(value['limit']) == int
            and 0 <= value['limit'] <= 100
            and type(value['fields']) == list
            and 1 <= len(value['fields']) <= LENGTHS['S']
            and all([
                (
                    self._validate_type_email(field)
                    or self._validate_type_option(field)
                    or self._validate_type_radio(field)
                    or self._validate_type_selection(field)
                    or self._validate_type_text(field)
                )
                for field
                in value['fields']
            ])
        )

    def _validate_type_email(self, value):
        """Validate that value is a correct email field specification"""
        keys = {'type', 'title', 'description', 'regex', 'hint'}
        return (
            type(value) is dict
            and set(value.keys()) == keys
            and value['type'] == 'email'
            and type(value['title']) == str
            and 1 <= len(value['title']) <= LENGTHS['S']
            and type(value['description']) == str
            and len(value['description']) <= LENGTHS['L']
            and type(value['regex']) == str
            and len(value['regex']) <= LENGTHS['M']
            and isregex(value['regex'])
            and type(value['hint']) == str
            and len(value['hint']) <= LENGTHS['S']
        )

    def _validate_type_option(self, value):
        """Validate that value is a correct option field specification"""
        keys = {'type', 'title', 'description', 'required'}
        return (
            type(value) is dict
            and set(value.keys()) == keys
            and value['type'] == 'option'
            and type(value['title']) == str
            and 1 <= len(value['title']) <= LENGTHS['S']
            and type(value['description']) == str
            and len(value['description']) <= LENGTHS['L']
            and type(value['required']) == bool
        )

    def _validate_type_radio(self, value):
        """Validate that value is a correct radio field specification"""
        keys = {'type', 'title', 'description', 'fields'}
        return (
            type(value) is dict
            and set(value.keys()) == keys
            and value['type'] == 'radio'
            and type(value['title']) == str
            and 1 <= len(value['title']) <= LENGTHS['S']
            and type(value['description']) == str
            and len(value['description']) <= LENGTHS['L']
            and type(value['fields']) == list
            and 1 <= len(value['fields']) <= LENGTHS['S']
            and all([
                self._validate_type_option(field)
                for field
                in value['fields']
            ])
        )

    def _validate_type_selection(self, value):
        """Validate that value is a correct selection field specification"""
        keys = {
            'type',
            'title',
            'description',
            'min_select',
            'max_select',
            'fields',
        }
        return (
            type(value) is dict
            and set(value.keys()) == keys
            and value['type'] == 'selection'
            and type(value['title']) == str
            and 1 <= len(value['title']) <= LENGTHS['S']
            and type(value['description']) == str
            and len(value['description']) <= LENGTHS['L']
            and type(value['fields']) == list
            and 1 <= len(value['fields']) <= LENGTHS['S']
            and all([
                self._validate_type_option(field)
                for field
                in value['fields']
            ])
            and type(value['min_select']) == type(value['max_select']) == int
            and 0 <= value['min_select'] <= value['max_select']
            and value['max_select'] <= len(value['fields'])
        )

    def _validate_type_text(self, value):
        """Validate that value is a correct text field specification"""
        keys = {'type', 'title', 'description', 'min_chars', 'max_chars'}
        return (
            type(value) is dict
            and set(value.keys()) == keys
            and value['type'] == 'text'
            and 1 <= len(value['title']) <= LENGTHS['S']
            and len(value['title']) <= LENGTHS['S']
            and type(value['description']) == str
            and len(value['description']) <= LENGTHS['L']
            and type(value['min_chars']) == type(value['max_chars']) == int
            and 0 <= value['min_chars'] <= value['max_chars']
            and value['max_chars'] <= LENGTHS['L']
        )


################################################################################
# Submission Validation
################################################################################


class SubmissionValidator(Validator):
    """The cerberus submission validator with added custom validation rules.

    For an explanation of the validation rules we kindly refer the curious
    reader to the FastSurvey and the cerberus documentations. They are omitted
    here to avoid documentation duplication and to keep the methods as
    overseeable as possible.

    """

    types_mapping = {
        'option': TypeDefinition('option', (bool,), ()),
        'text': TypeDefinition('text', (str,), ()),
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
            and re.match(REGEXES['email_address'], value)
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
