from flask_restful import marshal_with, fields, abort
from flask_login import current_user

from appname.api import Resource, BaseAPISchema, API_VERSION

class CurrentUserInfoSchema(BaseAPISchema):
    get_fields = {
        'id': fields.String,
        'email': fields.String,
        'full_name': fields.String,
    }

class CurrentUserInfo(Resource):
    schema = CurrentUserInfoSchema()

    @marshal_with(schema.get_fields)
    def get(self):
        if not current_user.is_authenticated:
            abort(401)
        return current_user
