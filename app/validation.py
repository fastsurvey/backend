from cerberus import Validator, TypeDefinition


mapping = Validator.types_mapping

mapping['Selection'] = TypeDefinition('Selection', (dict,), ())
mapping['Option'] = TypeDefinition('Option', (bool,), ())
mapping['DelimiterList'] = TypeDefinition('DelimiterList', (str,), ())
mapping['Text'] = TypeDefinition('Text', (str,), ())

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
                        'type': 'DelimiterList',
                    },
                },
            },
            'reason': {
                'type': 'Text',
            }
        },
    },
}

validator = Validator(schema, require_all=True)

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








'''

class Option(BaseModel):
    value bool = Field(...) 


class Radio(Field):

    def __init__(self, options):
        self.options = options

    def check(self):
        raise NotImplementedError


class Selection(Field):

    def __init__(self, min_selections, max_selections, options):
        self.min = min_selections
        self.max = max_selections
        self.options = options

    def check(self):
        raise NotImplementedError

'''
