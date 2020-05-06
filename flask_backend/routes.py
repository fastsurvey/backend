
from flask_backend import app, FRONTEND_URL, pending_entries_collection, verified_entries_collection, time_limits_collection
from flask_backend.surveys.survey_1 import survey_1_actions, survey_1_results
from flask_backend.surveys.survey_2 import survey_2_actions, survey_2_results
from flask_backend.surveys.survey_3 import survey_3_actions, survey_3_results
from flask_backend.surveys.survey_4 import survey_4_actions, survey_4_results
from flask_backend.surveys.survey_5 import survey_5_actions, survey_5_results

from flask_backend.support_functions import formatting

from flask import request, redirect


@app.route("/", methods=["GET"])
def backend_status():
    try:
        pending_entries_collection.count_documents()
        verified_entries_collection.count_documents()
        # TODO: Add test for sending mails
        return {"status": "all services operational"}, 200
    except:
        return {"status": "database error"}, 500


@app.route("/<survey_name>/submit", methods=["POST"])
def backend_submit(survey_name):

    if survey_name == "20200504":
        submit = survey_1_actions.submit
    elif survey_name == "fvv-ss20-referate":
        submit = survey_2_actions.submit
    elif survey_name == "fvv-ss20-go":
        submit = survey_3_actions.submit
    elif survey_name == "fvv-ss20-entlastung":
        submit = survey_4_actions.submit
    elif survey_name == "fvv-ss20-leitung":
        submit = survey_5_actions.submit
    else:
        return formatting.status("survey invalid"), 400

    # Checking whether the survey is currently open
    time_limit_record = time_limits_collection.find_one({"survey_name": survey_name})
    if time_limit_record is not None:
        if not time_limit_record["is_active"]:
            # Only when one has specifically set the survey
            # offline it does not accept a submisisson
            return formatting.status("survey closed"), 400

    request_dict = request.get_json(force=True)
    print(request_dict)

    result = submit(request_dict)
    print(result)
    return {"status": result["status"]}, result["status_code"]


@app.route("/<survey_name>/verify/<verification_token>", methods=["GET"])
def backend_verify(survey_name, verification_token):

    if survey_name == "20200504":
        verify = survey_1_actions.verify
    elif survey_name == "fvv-ss20-referate":
        verify = survey_2_actions.verify
    elif survey_name == "fvv-ss20-go":
        verify = survey_3_actions.verify
    elif survey_name == "fvv-ss20-entlastung":
        verify = survey_4_actions.verify
    elif survey_name == "fvv-ss20-leitung":
        verify = survey_5_actions.verify
    else:
        return formatting.status("survey invalid"), 400

    verify(verification_token)
    return redirect(f"{FRONTEND_URL}{survey_name}/success")


@app.route("/<survey_name>/results", methods=["GET"])
def backend_results(survey_name):

    if survey_name == "20200504":
        fetch = survey_1_results.fetch
    elif survey_name == "fvv-ss20-referate":
        fetch = survey_2_results.fetch
    elif survey_name == "fvv-ss20-go":
        fetch = survey_3_results.fetch
    elif survey_name == "fvv-ss20-entlastung":
        fetch = survey_4_results.fetch
    elif survey_name == "fvv-ss20-leitung":
        fetch = survey_5_results.fetch
    else:
        return formatting.status("survey invalid"), 400

    return fetch()
