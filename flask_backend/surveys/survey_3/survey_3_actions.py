

from flask_backend import pending_entries_collection, verified_entries_collection
from flask_backend.support_functions import formatting, mailing, tokening, timing
from flask_backend.surveys.survey_1.survey_1_validate import validate
from flask_backend.surveys.survey_1 import survey_1_format

from pymongo import DeleteMany, InsertOne


def submit(params_dict):

    validation_status = validate(params_dict)

    if validation_status["status"] != "ok":
        return validation_status

    # TODO: Only store the encrypted email address
    #       (one-way-encryption => hash-function)

    form_data = params_dict["form_data"]
    verification_token = tokening.generate_random_key()
    pending_entry = {
        "email": form_data["email"].lower(),
        "election": form_data["election"],
        "verification_token": verification_token,
        "survey": "fvv-ss20-go",
        "timestamp": timing.get_current_time()
    }

    mail_result = mailing.send_email(
        email=form_data["email"].lower(),
        form_data=survey_1_format.generate_form_data(form_data),
        change_url=survey_1_format.generate_change_url(form_data),
        verify_url=survey_1_format.generate_verify_url(verification_token),
        survey_name="Abstimmung zur neuen Geschäftsordnung, FVV SS20, 06.05.2020",
    )
    if mail_result:
        try:
            operations = [
                InsertOne(pending_entry)
            ]
            pending_entries_collection.bulk_write(operations, ordered=True)
            return formatting.status("ok", status_code=200)

        except Exception as e:
            return formatting.status("server error: communicating with database", status_code=500)
    else:
        return formatting.status("server error: sending the email", status_code=500)


def verify(verification_token):
    pending_entry = pending_entries_collection.find(
        {"verification_token": verification_token, "survey": "fvv-ss20-go"}
    )

    if pending_entry is not None:
        del pending_entry["verification_token"]
        operations = [
            DeleteMany({"email": pending_entry["email"], "survey": "fvv-ss20-go"}),
            InsertOne(pending_entry)
        ]
        verified_entries_collection.bulk_write(operations, ordered=True)
