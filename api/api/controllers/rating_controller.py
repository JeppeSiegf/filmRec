from flask import request
from flask_restx import Namespace, Resource, fields

from ..services.rating_service import RatingService

api = Namespace('ratings', description='Ratings operations')

rating_model = api.model('Rating', {
    'user_id': fields.String(description='The user unique identifier'),
    'film_id': fields.String(description='The film unique identifier'),
    'rating': fields.Integer(description='Numeric user score'),
    'liked': fields.Boolean(description='A like'),
    'rating_date': fields.DateTime(description='The date when the rating was last updated')
})

@api.route('/')
class RatingList(Resource):
    service = RatingService()

    @api.expect([rating_model])
    @api.marshal_list_with(rating_model, code=201)
    def post(self):
        """Bulk create or update ratings."""
        user_data = request.json

        if not isinstance(user_data, list) or not user_data:
            return {"message": "Invalid input. Expected a non-empty list of films."}, 400

        try:
            result = self.service.upsert_user_ratings(user_data)

            return result, 201

        except Exception as e:
            return {"message": f"Error processing films: {str(e)}"}, 500
