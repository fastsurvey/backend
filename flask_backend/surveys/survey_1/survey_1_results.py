
from flask_backend import verified_entries_collection
from flask_backend.support_functions import formatting

def fetch():
    verified_records = list(verified_entries_collection.find({"survey": "20200504"}))

    # Did not check for different email capitalizations in this survey yet
    # Back then "ge69zeh" and "GE69zeh" could vote twice
    # Here: Manual fix (faster)
    voter_emails = []

    electees = ["albers", "ballweg", "deniers", "schmidt"]
    results = {}
    for electee in ["albers", "ballweg", "deniers", "schmidt"]:
        results[electee] = 0

    for record in verified_records:
        if record["email"] not in voter_emails:
            for electee in ["albers", "ballweg", "deniers", "schmidt"]:
                results[electee] += 1 if record["election"][electee] else 0

    return formatting.status("ok", results=results)
