
from flask_backend.support_functions import timing
from datetime import datetime
from bson import ObjectId

def status(text, **kwargs):
    status_dict = {'status': text}
    status_dict.update(kwargs)
    return status_dict


def get_status_code(status):
    if status == "ok":
        return 200

    if status[:6] == "server":
        return 500

    if status[:6] == "email/" and status[-7:] == "invalid":
        return 401

    return 400

def postprocess_response(response_dict, new_api_key=None):
    status_code = get_status_code(response_dict["status"])
    if status_code != 200:
        result_dict = status(response_dict["status"])
        if "errors" in response_dict:
            result_dict.update({"errors": response_dict["errors"]})
        return result_dict, status_code

    if new_api_key is not None:
        response_dict.update({"api_key": new_api_key})

    return postprocess_json_encoding(response_dict), status_code

def postprocess_json_encoding(struct):
    if isinstance(struct, datetime):
        return timing.datetime_to_string(struct)

    if isinstance(struct, ObjectId):
        return str(struct)

    elif isinstance(struct, list):
        return [postprocess_json_encoding(element) for element in struct]

    elif isinstance(struct, dict):
        return {key: postprocess_json_encoding(struct[key]) for key in struct.keys()}

    else:
        return struct


server_error_helper_record = status('server error', details='helper record not found after successful authentication')


def strip_comma_text(text):
    if len(text) == 0:
        return text
    elif text[0] in (" ", ","):
        return strip_comma_text(text[1:])
    elif text[-1] in (" ", ","):
        return strip_comma_text(text[:-1])
    else:
        return text

def comma_text_to_list(text):
    text = strip_comma_text(text)
    names_list = [strip_comma_text(entry) for entry in text.split(",")]
    return list(filter(lambda x: x != "", names_list))

def uniquelify_list(old_list):
    new_list = []
    for element in old_list:
        if element not in new_list:
            new_list.append(element)
    return new_list
