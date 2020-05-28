from cerberus import Validator, TypeDefinition


class SubmissionValidator(Validator):

    types_mapping = Validator.types_mapping.copy()
    
    types_mapping['Selection'] = TypeDefinition('Selection', (dict,), ())
    types_mapping['List'] = TypeDefinition('List', (str,), ())
    types_mapping['Option'] = TypeDefinition('Option', (bool,), ())
    types_mapping['Text'] = TypeDefinition('Text', (str,), ())

    def _validate_min_chars(self, min_chars, field, value):
        """Validate the minimum length of the given input string

        The rule's arguments are validated against this schema:
        {'type': 'integer'}
        """
        if len(value) < min_chars:
            self._error(field, f'Must be longer than {min_chars} characters') 

    def _validate_min_select(self, min_select, field, value):
        """Validate the minimum number of selected items in a selection field

        The rule's arguments are validated against this schema:
        {'type': 'integer'}
        """
        pass

    def _validate_max_select(self, min_select, field, value):
        """Validate the minimum number of selected items in a selection field

        The rule's arguments are validated against this schema:
        {'type': 'integer'}
        """
        pass


schema = {
    'email': {
        'type': 'string',
        'regex': '^[a-z]{2}[0-9]{2}[a-z]{3}@mytum\.de$',
    },
    'properties': {
        'type': 'dict',
        'schema': {
            'election': {
                'type': 'Selection',
                'schema': {
                    'felix': {
                        'type': 'Option',
                    },
                    'moritz': {
                        'type': 'Option',
                    },
                    'andere': {
                        'type': 'List',
                    },
                },
            },
            'reason': {
                'type': 'Text',
                'min_chars': 10,
            }
        },
    },
}

validator = SubmissionValidator(schema, require_all=True)

dicto = {
    'email': 'gz43zuh@mytum.de',
    'properties': {
        'election': {
            'felix': True,
            'moritz': True,
            'andere': '',
        },
        'reason': 'hello world!',
    }
}

print(validator.validate(dicto))
