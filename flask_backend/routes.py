
from flask_backend import app, FRONTEND_URL, pending_entries_collection, verified_entries_collection, time_limits_collection
from flask_backend.surveys.survey_1 import survey_1_actions, survey_1_results

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
        return {"status": "database error"}, 200


@app.route("/<survey_date>/submit", methods=["POST"])
def backend_submit(survey_date):

    if survey_date == "20200504":
        submit = survey_1_actions.submit
    else:
        return formatting.status("survey invalid"), 400

    # Checking whether the survey is currently open
    time_limit_record = time_limits_collection.find_one({"survey_name": survey_date})
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


@app.route("/<survey_date>/verify/<verification_token>", methods=["GET"])
def backend_verify(survey_date, verification_token):

    if survey_date == "20200504":
        verify = survey_1_actions.verify
    else:
        return formatting.status("survey invalid")

    verify(verification_token)
    return redirect(f"{FRONTEND_URL}{survey_date}/success")


@app.route("/<survey_date>/results", methods=["GET"])
def backend_results(survey_date):

    if survey_date == "20200504":
        return survey_1_results.fetch()
    else:
        return formatting.status("survey invalid"), 400
