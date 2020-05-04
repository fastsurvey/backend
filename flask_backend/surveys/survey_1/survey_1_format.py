
from flask_backend import FRONTEND_URL, BACKEND_URL
from flask import render_template


def generate_form_data(form_data):
    return render_template("survey_1_email.html", election=form_data["election"])

def generate_change_url(form_data):
    change_url = f"{FRONTEND_URL}20200505/form?email={form_data['email']}"

    for name in ["albers", "deniers", "ballweg", "schmidt"]:
        change_url += f"&{name}={'true' if form_data['election'][name] else 'false'}"

    return change_url

def generate_verify_url(verification_token):
    return f"{BACKEND_URL}20200505/verify/{verification_token}"


if __name__ == "__main__":
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
