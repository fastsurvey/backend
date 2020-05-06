
from flask_backend import FRONTEND_URL, BACKEND_URL
from flask import render_template


def generate_form_data(form_data):
    return render_template("survey_5_email.html", election=form_data["election"])

def generate_change_url(form_data):
    change_url = f"{FRONTEND_URL}fvv-ss20-leitung/form?email={form_data['email']}"

    for electee in [
        "leitung.haver", "leitung.anhalt", "leitung.andere"
    ]:
        referat = electee.split('.')[0]
        name = electee.split('.')[1]

        if name == "andere":
            # form_data['election'][referat]["andere"] is a string
            change_url += f"&{name}={form_data['election'][referat][name]}"
        else:
            # every other field is a boolean
            change_url += f"&{name}={'true' if form_data['election'][referat][name] else 'false'}"

    return change_url

def generate_verify_url(verification_token):
    return f"{BACKEND_URL}fvv-ss20-leitung/verify/{verification_token}"

