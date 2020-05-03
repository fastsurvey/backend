
from flask_backend import app
from flask_backend.database import submit, verify
from flask import render_template, request, redirect


@app.route("/backend/submit", methods=["POST"])
def backend_submit_form_data():
    result = submit(request.get_json(force=True))
    print(result)
    return {"status": result["status"]}, result["status_code"]


@app.route("/backend/verify/<verification_token>", methods=["GET"])
def backend_verify_form_data(verification_token):
    verify(verification_token)
    return redirect("/success")


@app.errorhandler(404)
def page_not_found(e):
    # All the remaining routes are routed to the frontend production build
    return render_template("index.html")
