
from flask_backend import FRONTEND_URL, BACKEND_URL
from flask import render_template


def generate_form_data(form_data):
    return render_template("survey_2_email.html", election=form_data["election"])

def generate_change_url(form_data):
    change_url = f"{FRONTEND_URL}fvv-ss20-referate/form?email={form_data['email']}"

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

        if name.split('.')[1] == "andere":
            # form_data['election'][referat]["andere"] is a string
            change_url += f"&{name}={form_data['election'][referat][name]}"
        else:
            # every other field is a boolean
            change_url += f"&{name}={'true' if form_data['election'][referat][name] else 'false'}"

    return change_url

def generate_verify_url(verification_token):
    return f"{BACKEND_URL}fvv-ss20-referate/verify/{verification_token}"


if __name__ == "__main__":
    """
    example_3 = {
        'form-data': {
            'email': 'abcdefg@mytum.de',
            'election': {
                'albers': True,
                'deniers': True,
                'schmidt': False,
                'ballweg': False,
            }
        }
    }
    print(generate_change_url(example_3["form-data"]))
    print(generate_verify_url("dgshsbsjs"))
    """
    pass
