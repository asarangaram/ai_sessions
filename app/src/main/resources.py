from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, fields

from ..common.error_handler import custom_error_handler
from .model import LandingPageModel


class LandingPageResultSchema(Schema):
    name = fields.Str(required=True)
    info = fields.Str(required=True)


def register_main_resources(*, bp: Blueprint):
    @bp.route("/")
    class LandingPage(MethodView):
        @custom_error_handler
        @bp.response(200, LandingPageResultSchema)
        def get(self):
            page = LandingPageModel()
            return page
