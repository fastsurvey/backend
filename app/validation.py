from cerberus import Validator, TypeDefinition

from app.utils import isregex


class ConfigurationValidator(Validator):
    """The custom cerberus validator for validating survey configurations.

    TODO
    - finetune title/description/hint char limits with frontend
    - start <= end not validated

    """

    ADMIN_NAME_MIN_LENGTH, ADMIN_NAME_MAX_LENGTH = 1, 20
    SURVEY_NAME_MIN_LENGTH, SURVEY_NAME_MAX_LENGTH = 1, 20
    TITLE_MAX_LENGTH = 100  # all lengths are inclusive
    DESCRIPTION_MAX_LENGTH = 1000
    REGEX_MAX_LENGTH = 100
    HINT_MAX_LENGTH = 100
    TEXT_MAX_LENGTH = 10000

    SCHEMA = {
        'admin_name': {'type': 'string', 'minlength': 1, 'maxlength': 20},
        'survey_name': {'type': 'string', 'minlength': 1, 'maxlength': 20},
        'title': {'type': 'string', 'maxlength': TITLE_MAX_LENGTH},
        'description': {'type': 'string', 'maxlength': DESCRIPTION_MAX_LENGTH},
        'start': {'type': 'integer', 'min': 0},
        'end': {'type': 'integer', 'min': 0},
        'mode': {'type': 'integer', 'allowed': [0, 1, 2]},
        'fields': {
            'type': 'list',
            'schema': {'type': [
                'email',
                'option',
                'radio',
                'selection',
                'text',
            ]},
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
        return cls(cls.SCHEMA, require_all=True)


    ### CUSTOM TYPE VALIDATIONS ###


    def _validate_type_email(self, value):
        """Validate that value is a correct email field specification"""
        keys = {'type', 'title', 'description', 'regex', 'hint'}
        return (
            type(value) is dict
            and set(value.keys()) == keys
            and value['type'] == 'email'
            and type(value['title']) == str
            and len(value['title']) <= self.TITLE_MAX_LENGTH
            and type(value['description']) == str
            and len(value['description']) <= self.DESCRIPTION_MAX_LENGTH
            and type(value['regex']) == str
            and len(value['regex']) <= self.REGEX_MAX_LENGTH
            and isregex(value['regex'])
            and type(value['hint']) == str
            and len(value['hint']) <= self.HINT_MAX_LENGTH
        )

    def _validate_type_option(self, value):
        """Validate that value is a correct option field specification"""
        keys = {'type', 'title', 'description', 'mandatory'}
        return (
            type(value) is dict
            and set(value.keys()) == keys
            and value['type'] == 'option'
            and type(value['title']) == str
            and len(value['title']) <= self.TITLE_MAX_LENGTH
            and type(value['description']) == str
            and len(value['description']) <= self.DESCRIPTION_MAX_LENGTH
            and type(value['mandatory']) == bool
        )

    def _validate_type_radio(self, value):
        """Validate that value is a correct radio field specification"""
        keys = {'type', 'title', 'description', 'fields'}
        return (
            type(value) is dict
            and set(value.keys()) == keys
            and value['type'] == 'radio'
            and type(value['title']) == str
            and len(value['title']) <= self.TITLE_MAX_LENGTH
            and type(value['description']) == str
            and len(value['description']) <= self.DESCRIPTION_MAX_LENGTH
            and type(value['fields']) == list
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
            and len(value['title']) <= self.TITLE_MAX_LENGTH
            and type(value['description']) == str
            and len(value['description']) <= self.DESCRIPTION_MAX_LENGTH
            and type(value['fields']) == list
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
            and type(value['title']) == str
            and len(value['title']) <= self.TITLE_MAX_LENGTH
            and type(value['description']) == str
            and len(value['description']) <= self.DESCRIPTION_MAX_LENGTH
            and type(value['min_chars']) == type(value['max_chars']) == int
            and 0 <= value['min_chars'] <= value['max_chars']
            and value['max_chars'] <= self.TEXT_MAX_LENGTH
        )

    def _validate_type_configuration(self, value):
        """Validate that value is a correct survey configuration"""
        keys = {
            'admin_name',
            'survey_name',
            'title',
            'description',
            'start',
            'end',
            'mode',
            'fields',
        }
        return (
            type(value) is dict
            and set(value.keys()) == keys
            and type(value['admin_name']) == str
            and len(value['admin_name']) >= self.ADMIN_NAME_MIN_LENGTH
            and len(value['admin_name']) <= self.ADMIN_NAME_MAX_LENGTH
            and type(value['survey_name']) == str
            and len(value['survey_name']) >= self.SURVEY_NAME_MIN_LENGTH
            and len(value['survey_name']) <= self.SURVEY_NAME_MAX_LENGTH
            and type(value['title']) == str
            and len(value['title']) <= self.TITLE_MAX_LENGTH
            and type(value['description']) == str
            and len(value['description']) <= self.DESCRIPTION_MAX_LENGTH
            and type(value['start']) == type(value['end']) == int
            and value['start'] <= value['end']
            and value['mode'] in [0, 1, 2]
            and type(value['fields']) == list
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
        """Generate cerberus validation schema from a survey configuration."""

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
        """Count the number of selected options in a selection field."""
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
        if not self._validate_type_selection(value):
            return False
        if self._count_selections(value) != 1:
            return False
        return True


    ### CUSTOM VALIDATION RULES ###


    def _validate_min_chars(self, min_chars, field, value):
        """{'type': 'integer'}"""
        if len(value) < min_chars:
            self._error(field, f'must be at least {min_chars} characters long')

    def _validate_max_chars(self, max_chars, field, value):
        """{'type': 'integer'}"""
        if len(value) > max_chars:
            self._error(field, f'must be at most {max_chars} characters long')

    def _validate_min_select(self, min_select, field, value):
        """{'type': 'integer'}"""
        if self._count_selections(value) < min_select:
            self._error(field, f'must select at least {min_select} options')

    def _validate_max_select(self, max_select, field, value):
        """{'type': 'integer'}"""
        if self._count_selections(value) > max_select:
            self._error(field, f'must select at most {max_select} options')

    def _validate_mandatory(self, mandatory, field, value):
        """{'type': 'boolean'}"""
        if mandatory:
            if (
                type(value) is bool and not value
                or type(value) is str and value == ''
            ):
                self._error(field, f'this field is mandatory')
