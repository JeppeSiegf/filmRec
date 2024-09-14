from datetime import datetime

from flask_restx import Namespace, Resource, fields
from flask import request

from api.controllers.genre_controller import Genre
from api.services.film_service import FilmService
from api.models.film import Film

api = Namespace('films', description='Film operations')

#  Film model schema

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
    @api.param('search_query', 'The search query to filter films by title or other attributes')
    def get(self):
        """List all films or search for films"""
        search_query = request.args.get('search_query', '')  # Retrieve the query parameter
        films = FilmService.search_films(search_query)
        if films:
            return films
        api.abort(404, "No matching films found")


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
            last_update=datetime.now()
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