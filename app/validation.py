import re
import cerberus
import functools
import pydantic
import typing
import enum

import app.utils as utils


# string validation regexes
_REGEXES = {
    'email_address': r'^.+@.+$',
    'survey_name': r'^[a-z0-9-]{2,20}$',
}

# maximum character lengths (inclusive)
_LENGTHS = {
    'S': 128,
    'M': 1024,
    'L': 4096,
}



class Length(int, enum.Enum):
    A = 32
    B = 256
    C = 4096


class Pattern(str, enum.Enum):
    USERNAME = r'^[a-z0-9-]{1,32}$'
    SURVEY_NAME = r'^[a-z0-9-]{1,32}$'
    EMAIL_ADDRESS = r'^.+@.+$'


class BaseModel(pydantic.BaseModel):
    """Custom BaseModel that pydantic models inherit from."""

    class Config:
        max_anystr_length = Length.C
        extra = pydantic.Extra['forbid']


################################################################################
# Account Validation
################################################################################


class AccountData(BaseModel):
    """Pydantic model used to validate account data."""
    username: pydantic.constr(strict=True, regex=Pattern.USERNAME.value)
    password: pydantic.constr(strict=True, min_length=8, max_length=Length.B)
    email_address: pydantic.constr(
        strict=True,
        max_length=Length.B,
        regex=Pattern.EMAIL_ADDRESS.value,
    )


################################################################################
# Configuration Validation
################################################################################


class Field(BaseModel):
    title: pydantic.constr(strict=True, min_length=1, max_length=Length.B)
    description: pydantic.StrictStr


class EmailField(Field):
    type: typing.Literal['email']
    hint: pydantic.constr(strict=True, max_length=Length.B)
    regex: pydantic.constr(strict=True, max_length=Length.B)
    verify: pydantic.StrictBool

    @pydantic.validator('regex')
    def validate_regex(cls, v):
        try:
            re.compile(v)
            return v
        except:
            raise ValueError('invalid regular expression')


class OptionField(Field):
    type: typing.Literal['option']
    required: pydantic.StrictBool


class RadioField(Field):
    type: typing.Literal['radio']
    options: pydantic.conlist(
        item_type=pydantic.constr(
            strict=True,
            min_length=1,
            max_length=Length.B,
        ),
        min_items=1,
        max_items=Length.A,
    )


class SelectionField(Field):
    type: typing.Literal['selection']
    options: pydantic.conlist(
        item_type=pydantic.constr(
            strict=True,
            min_length=1,
            max_length=Length.B,
        ),
        min_items=1,
        max_items=Length.A,
    )
    min_select: pydantic.conint(strict=True, ge=0)
    max_select: pydantic.conint(strict=True, ge=0)

    @pydantic.validator('max_select')
    def validate_max_select(cls, v, values):
        if 'min_select' in values and v < values['min_select']:
            raise ValueError('max_select must be >= min_select')
        if 'options' in values and v > len(values['options']):
            raise ValueError('max must be <= number of options')
        return v


class TextField(Field):
    type: typing.Literal['text']
    min_chars: pydantic.conint(strict=True, ge=0, le=Length.C)
    max_chars: pydantic.conint(strict=True, ge=0, le=Length.C)

    @pydantic.validator('max_chars')
    def validate_max_chars(cls, v, values):
        if 'min_chars' in values and v < values['min_chars']:
            raise ValueError('max_chars must be >= min_chars')
        return v


class Configuration(Field):
    survey_name: pydantic.constr(strict=True, regex=Pattern.SURVEY_NAME.value)
    start: pydantic.conint(strict=True, ge=0, le=4102444800)
    end: pydantic.conint(strict=True, ge=0, le=4102444800)
    draft: pydantic.StrictBool
    limit: pydantic.conint(strict=True, ge=0)
    fields_: pydantic.conlist(
        item_type=typing.Union[
            EmailField,
            OptionField,
            RadioField,
            SelectionField,
            TextField,
        ],
        min_items=1,
        max_items=Length.A,
     ) = pydantic.Field(alias='fields')

    @pydantic.validator('end')
    def validate_end(cls, v, values):
        if 'start' in values and v < values['start']:
            raise ValueError('end must be >= start')
        return v

    @pydantic.validator('fields_')
    def validate_fields(cls, v):
        count = 0
        for field in v:
            if field.type == 'email' and field.verify:
                count += 1
        if count > 1:
            raise ValueError('only one email field with verification allowed')
        return v


class ConfigurationValidator():

    _FIELD_KEYS = {
        'configuration': {
            'survey_name',
            'title',
            'description',
            'start',
            'end',
            'draft',
            'limit',
            'fields',
        },
        'email': {'type', 'title', 'description', 'hint', 'verify', 'regex'},
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
                self._validate_email(field) and field['verify']
                for field
                in value['fields']
            ]) <= 1
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
            and type(value['hint']) is str
            and len(value['hint']) <= _LENGTHS['S']
            and type(value['verify']) is bool
            and type(value['regex']) is str
            and len(value['regex']) <= _LENGTHS['M']
            and utils.isregex(value['regex'])
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


def validate_option_field_submission(cls, v):
    if not v:
        raise ValueError('option is required')
    return v


def validate_selection_field_submission(cls, v):
    if len(set(v)) != len(v):
        raise ValueError('no duplicates allowed')
    return v


def build_email_field_validation(identifier, field, schema, validators):
    schema[identifier] = (
        pydantic.constr(
            strict=True,
            max_length=Length.B,
            # this regex checks if the string matches the regex defined in the
            # configurations, but also our (very loose) email regex
            regex=f'(?={Pattern.EMAIL_ADDRESS.value})(?={field.regex})',
        ),
        ...,
    )


def build_option_field_validation(identifier, field, schema, validators):
    schema[identifier] = (pydantic.StrictBool, ...)
    if field.required:
        validators[f'validate-{identifier}'] = (
            pydantic.validator(identifier, allow_reuse=True)(
                validate_option_field_submission,
            )
        )


def build_radio_field_validation(identifier, field, schema, validators):
    schema[identifier] = (
        typing.Literal[tuple(field.options)],
        ...,
    )


def build_selection_field_validation(identifier, field, schema, validators):
    schema[identifier] = (
        pydantic.conlist(
            item_type=typing.Literal[tuple(field.options)],
            min_items=field.min_select,
            max_items=field.max_select,
        ),
        ...,
    )
    validators[f'validate-{identifier}'] = (
        pydantic.validator(identifier, allow_reuse=True)(
            validate_selection_field_submission,
        )
    )


def build_text_field_validation(identifier, field, schema, validators):
    schema[identifier] = (
        pydantic.constr(
            strict=True,
            min_length=field.min_chars,
            max_length=field.max_chars,
        ),
        ...,
    )


def build_submission_model(configuration):
    """Build pydantic submission model based on the survey configuration."""
    schema = dict()
    validators = dict()
    mapping = dict(
        email=build_email_field_validation,
        option=build_option_field_validation,
        radio=build_radio_field_validation,
        selection=build_selection_field_validation,
        text=build_text_field_validation,
    )
    for identifier, field in enumerate(configuration.fields_):
        mapping[field.type](str(identifier), field, schema, validators)
    return pydantic.create_model(
        'Submission',
        **schema,
        __base__=BaseModel,
        __validators__=validators,
    )






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
            and len(value) <= _LENGTHS['M']
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
