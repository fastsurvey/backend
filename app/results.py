class Alligator:
    """Does it aggregate ... or does it alligate ... ?"""

    def __init__(self, configuration, database):
        """Initialize alligator with some pipeline parts already defined."""
        self.configuration = configuration
        self.verified = database[f"{self.configuration['_id']}.verified"]
        self.results = database['results']
        self.mapping = {
            'Radio': self._add_radio,
            'Selection': self._add_selection,
            'Text': self._add_text,
        }
        self.project = {}
        self.group = {
            '_id': self.configuration['_id'],
            'count': {'$sum': 1},
        }
        self.merge = {
            'into': 'results',
            'on': '_id',
            'whenMatched': 'replace',
            'whenNotMatched': 'insert',
        }

    def _add_radio(self, field, index):
        """Add commands to deal with radio field to results pipeline."""
        subfields = field['properties']['fields']
        for i in range(len(subfields)):
            path = f'properties.{index}.{i+1}'
            self.project[path] = {'$toInt': f'${path}'}
            self.group[f'{index}-{i+1}'] = {'$sum': f'${path}'}

    def _add_selection(self, field, index):
        """Add commands to deal with selection field to results pipeline."""
        self._add_radio(field, index)

    def _add_text(self, field, index):
        """Add commands to deal with text field to results pipeline."""
        pass

    def _build_pipeline(self):
        """Build the aggregation pipeline used in pymongo's aggregate call."""
        for index, field in enumerate(self.configuration['fields']):
            self.mapping[field['type']](field, index+1)
        pipeline = []
        if self.project:
            pipeline.append({'$project': self.project})
        pipeline.append({'$group': self.group})
        pipeline.append({'$merge': self.merge})
        return pipeline

    async def fetch(self):
        """Aggregate and return the results of the survey."""
        results = await self.results.find_one(
            {'_id': self.configuration['_id']},
        )
        if results:
            return results
        cursor = self.verified.aggregate(
            pipeline=self._build_pipeline(),
            allowDiskUse=True,
        )
        # this is needed to make sure that the aggregation finished
        async for _ in cursor: pass
        return await self.results.find_one({'_id': self.configuration['_id']})
