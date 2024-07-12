from flask_restx import Namespace, Resource, fields
from flask import request
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

    @api.expect(user_model)
    @api.marshal_with(user_model, code=201)
    def post(self):
        """Create a new user"""
        data = request.json
        return UserService.create_user(data['username']), 201

@api.route('/<int:id>')
@api.response(404, 'User not found')
@api.param('id', 'The user identifier')
class User(Resource):
    @api.marshal_with(user_model)
    def get(self, id):
        """Fetch a user given its identifier"""
        user = UserService.get_user_by_id(id)
        if user:
            return user
        api.abort(404)

    @api.expect(user_model)
    @api.marshal_with(user_model)
    def put(self, id):
        """Update a user given its identifier"""
        data = request.json
        return UserService.update_user(id, data.get('username'))

    @api.response(204, 'User deleted')
    def delete(self, id):
        """Delete a user given its identifier"""
        UserService.delete_user(id)
        return '', 204
