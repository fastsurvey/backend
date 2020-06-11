from flask import Flask
from flask_cors import CORS
import os
import json

app = Flask(__name__)
app.config['REMEMBER_COOKIE_DURATION'] = 60 * 60 * 24 * 1
cors = CORS(app)


@app.route("/<username>/<surveyname>", methods=["GET"])
def fetch_config(username, surveyname):
    survey_configs = os.listdir("./surveys")
    if f"{username}.{surveyname}.json" in survey_configs:
        with open(f"./surveys/{username}.{surveyname}.json", "r") as survey_config:
            return {'status': 'ok', 'config': json.loads(survey_config.read())}, 200

    return {'status': 'survey not found'}, 404


app.run(debug=True)
