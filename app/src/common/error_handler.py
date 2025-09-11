from collections import OrderedDict
from functools import wraps

from flask import request
from marshmallow import ValidationError
from werkzeug.exceptions import InternalServerError, NotFound

enableLogging = False


def custom_error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if enableLogging:
            form_data = request.form.to_dict()
            print(f"Incoming Request Data: {form_data}")
        try:
            return func(*args, **kwargs)
        except Exception as err:
            response = OrderedDict()
            response["type"] = type(err).__name__  # e.g. "ValueError"
            if isinstance(err, ValidationError):
                for k, v in err.messages.items():
                    response[k] = v
                response["code"] = 422
            elif isinstance(err, NotFound):
                response["error"] = {"error": str(err)}
                response["code"] = 404
            elif isinstance(err, InternalServerError):
                response["error"] = {"error": str(err)}
                response["code"] = 500
            else:
                response["error"] = {"error": str(err)}
                response["code"] = 500

            return response, response["code"]

    return wrapper
