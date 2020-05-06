
from flask_backend import FRONTEND_URL, BACKEND_URL
from flask import render_template


def generate_form_data(form_data):
    return render_template("survey_4_email.html", election=form_data["election"])

def generate_change_url(form_data):
    change_url = f"{FRONTEND_URL}fvv-ss20-leitung/form?email={form_data['email']}"

    for key in ["ja", "nein", "enthaltung"]:
        change_url += f"&{key}={'true' if form_data['election'][key] else 'false'}"

    return change_url

def generate_verify_url(verification_token):
    return f"{BACKEND_URL}fvv-ss20-leitung/verify/{verification_token}"


