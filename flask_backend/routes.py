
from flask_backend import app, FRONTEND_URL
from flask_backend.surveys.survey_1 import survey_1_actions

from flask_backend.support_functions import formatting

from flask import request, redirect


@app.route("/<survey_date>/submit", methods=["POST"])
def backend_submit_form_data(survey_date):

    if survey_date == "20200505":
        submit = survey_1_actions.submit
    else:
        return formatting.status("invalid survey"), 400

    request_dict = request.get_json(force=True)
    print(request_dict)

    result = submit(request_dict)
    print(result)
    return {"status": result["status"]}, result["status_code"]


@app.route("/<survey_date>/verify/<verification_token>", methods=["GET"])
def backend_verify_form_data(survey_date, verification_token):

    if survey_date == "20200505":
        verify = survey_1_actions.verify
    else:
        return formatting.status("invalid survey")

    verify(verification_token)
    return redirect(f"{FRONTEND_URL}{survey_date}/success")
