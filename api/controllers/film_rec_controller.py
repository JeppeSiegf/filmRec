
from flask_restx import Namespace, Resource, fields
from flask import request
from api.services.film_rec_service import Film_Rec_Service

api = Namespace('recommendations', description='Film rec operations')

film_model = api.model('Film', {
    'page_ref': fields.String(required=True, description='Reference URL for the film'),
    'image_ref': fields.String(description='Image Reference URL for the film'),
    'title': fields.String(description='The film title'),
    'release_year': fields.Integer(description='Year of release'),
    'directors': fields.List(fields.String, description='List of director names'),

})
@api.route('/')
class FilmList(Resource):
    @api.marshal_list_with(film_model)
    @api.param('search_query', 'The search query to filter films by title or other attributes')
    def get(self):
        """List all films or search for films"""
        film_ref = request.args.get('search_query', '')  # Retrieve the query parameter
        films = Film_Rec_Service.get_films_reccomendations(film_ref)  # Call the service method synchronously
        if films:
            return films
        api.abort(404, "No matching films found")