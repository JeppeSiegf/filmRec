from flask import request
from flask_restx import Namespace, Resource, fields

from ..services.user_service import UserService

api = Namespace('users', description='User operations')

user_model = api.model('User', {
    'id': fields.Integer(readonly=True, description='The user unique identifier'),
    'username': fields.String(required=True, description='The user username'),
    'last_update': fields.DateTime(description='The date when the user was last updated')
})


@api.route('/')
class UserList(Resource):
    service = UserService()

    @api.expect([user_model], validate=True)
    @api.marshal_with(user_model, code=201)
    def post(self):
        """Bulk create or update films."""
        user_data = request.json  # Expecting a list of film objects

        if not isinstance(user_data, list) or not user_data:
            return {"message": "Invalid input. Expected a non-empty list of films."}, 400

        try:
            # Call your service method to bulk upsert films
            result = self.service.create_multiple_users(user_data)

            return result, 201

        except Exception as e:
            return {"message": f"Error processing films: {str(e)}"}, 500



