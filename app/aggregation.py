from app.utils import combine
from app.resources.database import database


class Alligator:
    """Does it aggregate ... or does it alligate ... ?"""

    def __init__(self, configuration):
        """Initialize alligator with some pipeline parts already defined."""
        self.configuration = configuration
        self.survey_id = combine(
            configuration['username'],
            configuration['survey_name'],
        )
        self.collection = (
            database.database[f'surveys.{self.survey_id}.submissions']
            if self.configuration['authentication'] == 'open'
            else database.database[f'surveys.{self.survey_id}.verified-submissions']
        )
        self.resultss = database.database['resultss']
        self.mapping = {
            'email': self._add_email,
            'option': self._add_option,
            'radio': self._add_radio,
            'selection': self._add_selection,
            'text': self._add_text,
        }
        self.project = {}
        self.group = {
            '_id': self.survey_id,
            'count': {'$sum': 1},
        }
        self.merge = {
            'into': 'resultss',
            'on': '_id',
            'whenMatched': 'replace',
            'whenNotMatched': 'insert',
        }

    def _add_email(self, field, index):
        """Add commands to deal with email field to results pipeline."""
        pass

    def _add_option(self, field, index):
        """Add commands to deal with option field to results pipeline."""
        path = f'data.{index}'
        self.project[path] = {'$toInt': f'${path}'}
        self.group[str(index)] = {'$sum': f'${path}'}

    def _add_radio(self, field, index):
        """Add commands to deal with radio field to results pipeline."""
        subfields = field['fields']
        for i in range(len(subfields)):
            path = f'data.{index}.{i+1}'
            self.project[path] = {'$toInt': f'${path}'}
            self.group[f'{index}+{i+1}'] = {'$sum': f'${path}'}

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

    def _restructure(self, results):
        """Make planar results from MongoDB aggregation nested."""
        e = {}
        for key, value in results.items():
            if '+' in key:
                split = key.split('+', maxsplit=1)
                e.setdefault(split[0], {})
                e[split[0]][split[1]] = value
            else:
                e[key] = value
        return e

    async def fetch(self):
        """Aggregate and return the results of the survey."""
        results = await self.resultss.find_one(
            filter={'_id': self.survey_id},
            projection={'_id': False},
        )
        if results is None:


            # TODO do something if there are no submissions
            # maybe it's better to simply check if the collection exists?
            if await self.collection.count_documents({}) == 0: return {}


            cursor = self.collection.aggregate(
                pipeline=self._build_pipeline(),
                allowDiskUse=True,
            )
            async for _ in cursor: pass  # make sure that aggregation finished
            results = await self.resultss.find_one(
                filter={'_id': self.survey_id},
                projection={'_id': False},
            )
        return self._restructure(results)
