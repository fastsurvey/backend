
from flask_backend import verified_entries_collection
from flask_backend.support_functions import formatting

def fetch():
    verified_records = list(verified_entries_collection.find({"survey": "fvv-ss20-leitung"}))

    results = {}

    for electee in [
        "leitung.haver", "leitung.anhalt", "leitung.andere"
    ]:
        referat = electee.split('.')[0]
        name = electee.split('.')[1]

        if referat not in results:
            results[referat] = {}

        if name == "andere":
            results[referat][name] = {}
        else:
            results[referat][name] = 0

    # Why do I not use .count_documents ?
    # 27 queries to gcp take a while + since the backend is not
    # asyncronous yet, this way is even more computationally efficient

    for record in verified_records:
        for electee in [
            "leitung.haver", "leitung.anhalt", "leitung.andere"
        ]:
            referat = electee.split('.')[0]
            name = electee.split('.')[1]

            if name == "andere":
                # List already made unique
                andere_list = record['election'][referat]["andere"]
                for andere in andere_list:
                    if andere not in results[referat]["andere"]:
                        results[referat]["andere"][andere] = 0
                    results[referat]["andere"][andere] += 1
            else:
                results[referat][name] += 1 if record['election'][referat][name] else 0

    return formatting.status("ok", results=results)
