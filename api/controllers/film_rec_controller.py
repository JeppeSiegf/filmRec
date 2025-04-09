from flask_restx import Namespace, Resource, fields
from flask import request

from api.controllers.api_models import film_model
from api.services.film_rec_service import Film_Rec_Service

api = Namespace('recommendations', description='Film rec operations')


@api.route('/')
class FilmList(Resource):
    @api.marshal_list_with(film_model)
    @api.param('page_ref', 'The Reference to film which the recommendation should be based on')
    def get(self):
        film_ref = request.args.get('page_ref')

        if not film_ref:  # Ensure page_ref is provided
            api.abort(400, "Missing 'page_ref' parameter")

        films = Film_Rec_Service.get_films_recommendations(film_ref, 12)

        if films:
            return films
        api.abort(404, "No recommendations found")
