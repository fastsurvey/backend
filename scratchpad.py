import secrets

with open('/usr/share/dict/words') as f:
    words = [word.strip().lower() for word in f]
    password = '-'.join(secrets.choice(words) for i in range(4))
    print(password)






'''

New Submission Structure:

    [
        "test+0@fastsurvey.io",
        true,
        [false, false, false, true],
        [true, false, true],
        "It keeps my head cool while I answer tricky surveys."
    ]

New Radio/Selection Configuration Structure:

    {
        "type": "radio",
        "title": "What's your favorite fruit?",
        "description": "",
        "fields": ["Asparagus", "Spinach", "Artichoke", "None of these is a fruit"]
    }

'''









# motor transaction example

'''

async with await main.motor_client.start_session() as session:
    async with session.start_transaction():
        #await main.database['toast'].rename('toast-reloaded')
        #await main.database['toast-reloaded'].insert_one({'value': 'hello!'})
        #await main.database['toast-reloaded'].rename('toast-reloaded-two')
        #await main.database['toast-reloaded-two'].drop()
        #await main.database['japan'].insert_one({'value': 'what?'})
        result = await main.database['japan'].replace_one(
            filter={'value': 'what?'},
            replacement={'password': 'lol'},
        )
        await main.database['japan'].insert_one({'value': result.matched_count})


async with await self.motor_client.start_session() as session:
    async with session.start_transaction():

        # TODO rename results

        result = await self.database['configurations'].replace_one(
            filter=expression,
            replacement=configuration,
        )
        if result.matched_count == 0:
            raise HTTPException(400, 'not an existing survey')

        collection_names = await self.database.list_collection_names()
        old_cname = (
            f'surveys'
            f'.{combine(username, survey_name)}'
            f'.submissions'
        )
        new_cname = (
            f'surveys'
            f'.{combine(username, configuration["survey_name"])}'
            f'.submissions'
        )
        if old_cname in collection_names:
            self.database[old_cname].rename(new_cname)

        old_cname = f'{old_cname}.verified'
        new_cname = f'{new_cname}.verified'
        if old_cname in collection_names:
            self.database[old_cname].rename(new_cname)

'''
