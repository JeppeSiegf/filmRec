from flask import request
from flask_restx import Namespace, Resource, fields

from api.services.user_service import UserService

api = Namespace('users', description='User operations')

user_model = api.model('User', {
    'id': fields.Integer(readonly=True, description='The user unique identifier'),
    'username': fields.String(required=True, description='The user username'),
    'last_update': fields.DateTime(description='The date when the user was last updated')
})


@api.route('/')
class UserList(Resource):
    @api.marshal_list_with(user_model)
    def get(self):
        """List all users"""
        return UserService.get_all_users()




