from flask_restx import Namespace, Resource, fields
from flask import request

from api.controllers.genre_controller import Genre
from api.services.film_service import FilmService
from api.models.film import Film

api = Namespace('films', description='Film operations')

# Define the film_model according to the updated schema

film_model = api.model('Film', {
    'page_ref': fields.String(required=True, description='Reference URL for the film'),
    'image_ref': fields.String(description='Image Reference URL for the film'),
    'id': fields.Integer(readonly=True, description='The film unique identifier'),
    'title': fields.String(description='The film title'),
    'total_watches': fields.Integer(description='Total watches of the film'),
    'last_update': fields.Date(description='Last update date of the film'),
    'release_year': fields.Integer(description='Year of release'),

})
@api.route('/')
class FilmList(Resource):
    @api.marshal_list_with(film_model)
    def get(self):
        """List all films"""
        return FilmService.get_all_films()

    @api.expect(film_model)
    @api.marshal_with(film_model, code=201)
    def post(self):
        """Create a new film"""
        data = request.json
        genres = data.get('genres', [])

        film = Film(
            page_ref=data['page_ref'],
            image_ref=data.get('image_ref'),
            title=data.get('title'),
            total_watches=data.get('total_watches', 0),
            last_update=data.get('last_update'),
            release_year=data.get('release_year'),
            # Assuming genres is a list of genre identifiers or names
            # Note: You may need to process genres to link them to actual Genre instances
             # Adjust according to your Genre model
        )
        created_film = FilmService.create_film(film)
        return created_film, 201

@api.route('/<string:page_ref>')
@api.response(404, 'Film not found')
@api.param('page_ref', 'The film reference')
class FilmResource(Resource):
    @api.marshal_with(film_model)
    def get(self, page_ref):
        """Fetch a film given its reference"""
        film = FilmService.get_film_by_page_ref(page_ref)
        if film:
            return film
        api.abort(404, "Film not found")