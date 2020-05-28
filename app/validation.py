from cerberus import Validator, TypeDefinition


class SubmissionValidator(Validator):

    types_mapping = Validator.types_mapping.copy()
    
    types_mapping['Selection'] = TypeDefinition('Selection', (dict,), ())
    types_mapping['List'] = TypeDefinition('List', (str,), ())
    types_mapping['Option'] = TypeDefinition('Option', (bool,), ())
    types_mapping['Text'] = TypeDefinition('Text', (str,), ())
    
    def __init__(self, template, *args, **kwargs):
        schema = SubmissionValidator._generate_schema(template)
        super(SubmissionValidator, self).__init__(
            schema, 
            *args, 
            **kwargs
        )

        import json
        print(json.dumps(schema, sort_keys=True, indent=4))

    @staticmethod
    def _generate_schema(template):

        def _generate_field_schema(field):
            fs = {'type': field['type']}
            if 'properties' in field.keys():
                if 'fields' in field['properties'].keys():
                    fs['schema'] = {
                        child['identifier']: _generate_field_schema(child)
                        for child
                        in field['properties'].pop('fields')
                    }
                for k, v in field['properties'].items():
                    fs[k] = v
            return fs

        schema = {
            'email': {
                'type': 'string',
                'regex': '^[a-z]{2}[0-9]{2}[a-z]{3}@mytum\.de$',
            },
            'properties': {
                'type': 'dict',
                'schema': {
                    field['identifier']: _generate_field_schema(field)
                    for field
                    in template['fields']
                },
            },
        }
        return schema

    def _validate_min_chars(self, min_chars, field, value):
        """Validate the minimum length (inclusive) of the given input string

        The rule's arguments are validated against this schema:
        {'type': 'integer'}
        """
        if len(value) < min_chars:
            self._error(field, f'Must be at least {min_chars} characters long') 
  
    def _validate_max_chars(self, max_chars, field, value):
        """Validate the maximum length (inclusive) of the given input string

        The rule's arguments are validated against this schema:
        {'type': 'integer'}
        """
        if len(value) >= max_chars:
            self._error(field, f'Must be at most {max_chars} characters long') 

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




template = {
    "title": "Survey to test backend functionality",
    "description": "...",
    "start": 1589805200,
    "end": 1989805200,
    "fields": [
        {
            "identifier": "election",
            "description": "Who will be the next president?",
            "type": "Selection",
            "properties": {
                "min_select": 0,
                "max_select": 2,
                "fields": [
                    {
                        "identifier": "felix",
                        "description": "Felix Böhm",
                        "type": "Option"
                    },
                    {
                        "identifier": "moritz",
                        "description": "Moritz Makowski",
                        "type": "Option"
                    },
                    {
                        "identifier": "andere",
                        "description": "Andere",
                        "type": "List"
                    }
                ]
            }
        },
        {
            "identifier": "reason",
            "description": "The reason for your choice",
            "type": "Text",
            "properties": {
                "min_chars": 10,
                "max_chars": 100
            }
        }
    ]
}

'''
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
'''

validator = SubmissionValidator(template, require_all=True)

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
