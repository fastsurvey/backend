
from flask_backend import verified_entries_collection
from flask_backend.support_functions import formatting

def fetch():
    verified_records = list(verified_entries_collection.find({"survey": "fvv-ss20-go"}))

    # Did not check for different email capitalizations in this survey yet
    # Back then "ge69zeh" and "GE69zeh" could vote twice
    # Here: Manual fix (faster)
    voter_emails = []

    options = ["ja", "nein", "enthaltung"]
    results = {}
    for option in options:
        results[option] = 0

    for record in verified_records:
        if record["email"] not in voter_emails:
            for option in options:
                results[option] += 1 if record["election"][option] else 0

    return formatting.status("ok", results=results)
