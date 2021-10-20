import pydantic
import typing
import re
import enum


################################################################################
# Constants
################################################################################


class Length(int, enum.Enum):
    A = 32
    B = 256
    C = 4096
    D = 65536


class Pattern(str, enum.Enum):
    USERNAME = r'^[a-z0-9-]{1,32}$'
    SURVEY_NAME = r'^[a-z0-9-]{1,32}$'
    EMAIL_ADDRESS = r'^.+@.+$'


################################################################################
# Custom Types
################################################################################


Username = pydantic.constr(strict=True, regex=Pattern.USERNAME.value)
SurveyName = pydantic.constr(strict=True, regex=Pattern.SURVEY_NAME.value)
Password = pydantic.constr(strict=True, min_length=8, max_length=Length.B)
Token = pydantic.constr(strict=True, min_length=64, max_length=64)
EmailAddress = pydantic.constr(
    strict=True,
    max_length=Length.B,
    regex=Pattern.EMAIL_ADDRESS.value,
)
Timestamp = pydantic.conint(strict=True, ge=0, le=4102444800)


################################################################################
# Base Model
################################################################################


class BaseModel(pydantic.BaseModel):
    """Custom BaseModel that pydantic models inherit from."""

    class Config:
        max_anystr_length = Length.C
        extra = pydantic.Extra['forbid']


################################################################################
# Account Data
################################################################################


class AccountData(BaseModel):
    """Pydantic model used to validate account data."""
    username: Username
    email_address: EmailAddress
    password: Password


class AccountDataUpdate(BaseModel):
    """Pydantic model used to validate updates to the account data."""
    username: Username
    email_address: EmailAddress
    password: Password = None


################################################################################
# Survey Configuration
################################################################################


class Field(BaseModel):
    identifier: pydantic.conint(strict=True, ge=0, le=Length.D)
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

    @pydantic.validator('options')
    def validate_options(cls, v):
        if len(set(v)) < len(v):
            raise ValueError('options must be unique')
        return v


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
    max_select: pydantic.conint(strict=True, ge=1)

    @pydantic.validator('options')
    def validate_options(cls, v):
        if len(set(v)) < len(v):
            raise ValueError('options must be unique')
        return v

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


class Configuration(BaseModel):
    survey_name: SurveyName
    title: pydantic.constr(strict=True, min_length=1, max_length=Length.B)
    description: pydantic.StrictStr
    start: typing.Optional[Timestamp] = pydantic.Field(...)
    end: typing.Optional[Timestamp] = pydantic.Field(...)
    draft: pydantic.StrictBool
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
        if 'start' in values and values['start'] is not None:
            if v is not None and v < values['start']:
                raise ValueError('end must be >= start')
        return v

    @pydantic.validator('fields_')
    def validate_fields(cls, v):
        identifiers = set()
        count = 0
        for field in v:
            identifiers.add(field.identifier)
            if field.type == 'email' and field.verify:
                count += 1
        if len(identifiers) < len(v):
            raise ValueError('field identifiers have to be unique')
        if count > 1:
            raise ValueError('only one email field with verification allowed')
        return v


################################################################################
# Survey Submission
################################################################################


def validate_option_field_submission(cls, v):
    if not v:
        raise ValueError('option is required')
    return v


def validate_selection_field_submission(cls, v):
    if len(set(v)) < len(v):
        raise ValueError('no duplicate selections allowed')
    return v


def build_email_field_validation(identifier, field, schema, validators):
    schema[identifier] = (
        pydantic.constr(
            strict=True,
            max_length=Length.B,
            # this regex checks if the string matches the regex defined in the
            # configurations, but also our (very loose) email regex
            regex=f'(?={Pattern.EMAIL_ADDRESS.value})(?={field["regex"]})',
        ),
        ...,
    )


def build_option_field_validation(identifier, field, schema, validators):
    schema[identifier] = (pydantic.StrictBool, ...)
    if field['required']:
        validators[f'validate-{identifier}'] = (
            pydantic.validator(identifier, allow_reuse=True)(
                validate_option_field_submission,
            )
        )


def build_radio_field_validation(identifier, field, schema, validators):
    schema[identifier] = (
        typing.Literal[tuple(field['options'])],
        ...,
    )


def build_selection_field_validation(identifier, field, schema, validators):
    schema[identifier] = (
        pydantic.conlist(
            item_type=typing.Literal[tuple(field['options'])],
            min_items=field['min_select'],
            max_items=field['max_select'],
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
            min_length=field['min_chars'],
            max_length=field['max_chars'],
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
    for field in configuration['fields']:
        identifier = str(field['identifier'])
        mapping[field['type']](identifier, field, schema, validators)
    return pydantic.create_model(
        'Submission',
        **schema,
        __base__=BaseModel,
        __validators__=validators,
    )


################################################################################
# Other Models
################################################################################


class AuthenticationCredentials(BaseModel):
    identifier: typing.Union[Username, EmailAddress]
    password: Password


class VerificationCredentials(BaseModel):
    verification_token: Token
