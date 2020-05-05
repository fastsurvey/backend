
from flask_backend import verified_entries_collection
from flask_backend.support_functions import formatting

def fetch():
    verified_records = list(verified_entries_collection.find({"survey": "fss-ss20-referate"}))

    electees = ["albers", "ballweg", "deniers", "schmidt"]
    results = {}

    for electee in [
        "erstsemester.koenigbaur", "erstsemester.wernsdorfer", "erstsemester.andere",
        "veranstaltungen.ritter", "veranstaltungen.pro", "veranstaltungen.andere",
        "skripte.lukasch", "skripte.limant", "skripte.andere",
        "quantum.albrecht", "quantum.roithmaier", "quantum.andere",
        "kooperationen.winckler", "kooperationen.andere",
        "it.kalk", "it.sittig", "it.andere",
        "evaluationen.reichelt", "evaluationen.andere",
        "hochschulpolitik.armbruster", "hochschulpolitik.paulus", "hochschulpolitik.andere",
        "finanzen.spicker", "finanzen.schuh", "finanzen.andere",
        "pr.werle", "pr.andere",
    ]:
        referat = electee.split('.')[0]
        name = electee.split('.')[1]

        if referat not in results:
            results[referat] = {}

        if name == "andere":
            results[referat][name] = []
        else:
            results[referat][name] = 0

    # Why do I not use .count_documents ?
    # 27 queries to gcp take a while + since the backend is not
    # asyncronous yet, this way is even more computationally efficient

    for record in verified_records:
        for electee in [
            "erstsemester.koenigbaur", "erstsemester.wernsdorfer", "erstsemester.andere",
            "veranstaltungen.ritter", "veranstaltungen.pro", "veranstaltungen.andere",
            "skripte.lukasch", "skripte.limant", "skripte.andere",
            "quantum.albrecht", "quantum.roithmaier", "quantum.andere",
            "kooperationen.winckler", "kooperationen.andere",
            "it.kalk", "it.sittig", "it.andere",
            "evaluationen.reichelt", "evaluationen.andere",
            "hochschulpolitik.armbruster", "hochschulpolitik.paulus", "hochschulpolitik.andere",
            "finanzen.spicker", "finanzen.schuh", "finanzen.andere",
            "pr.werle", "pr.andere",
        ]:
            referat = electee.split('.')[0]
            name = electee.split('.')[1]

            if name.split('.')[1] != "andere":
                results[referat][name] += 1 if record['election'][referat][name] else 0

            # TODO: Also count "andere" values

    return formatting.status("ok", results=results)
