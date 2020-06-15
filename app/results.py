class Alligator:
    """Does it aggregate ... or does it alligate ... ?"""

    def __init__(self, configuration, database):
        self.cn = configuration
        self.verified = database[f"{self.cn['_id']}.verified"]
        self.results = database['results']
        self.mapping = {
            'Radio': self._add_radio,
            'Selection': self._add_selection,
            'Text': self._add_text,
        }
        self.project = {}
        self.group = {
            '_id': self.cn['_id'],
            'count': {'$sum': 1},
        }
        self.merge = {
            'into': 'results',
            'on': '_id',
            'whenMatched': 'replace',
            'whenNotMatched': 'insert',
        }
   
    def _add_radio(self, field, index):
        subfields = field['properties']['fields']
        for i in range(len(subfields)):
            path = f'properties.{index}.{i+1}'
            self.project[path] = {'$toInt': f'${path}'}
            self.group[f'{index}-{i+1}'] = {'$sum': f'${path}'}

    def _add_selection(self, field, index):
        pass

    def _add_text(self, field, index):
        pass

    def _build_pipeline(self):
        """Build the aggregation pipeline used in pymongo's aggregate call."""
        for index, field in enumerate(self.cn['fields']):
            self.mapping[field['type']](field, index+1)
        pipeline = []
        if self.project:
            pipeline.append({'$project': self.project})
        pipeline.append({'$group': self.group})
        pipeline.append({'$merge': self.merge})
        return pipeline

    async def fetch(self):
        results = await self.results.find_one(self.cn['_id'])
        if results is not None:
            return results
        cursor = self.verified.aggregate(
            pipeline=self._build_pipeline(),
            allowDiskUse=True,
        )
        async for _ in cursor: pass
        return await self.results.find_one(self.cn['_id'])
