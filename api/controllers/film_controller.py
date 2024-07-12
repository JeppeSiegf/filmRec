from flask_restx import Namespace, Resource, fields
from flask import request
from api.services.film_service import FilmService

api = Namespace('films', description='Film operations')

film_model = api.model('Film', {
    'id': fields.Integer(readonly=True, description='The film unique identifier'),
    'title': fields.String(required=True, description='The film title'),
    'release_year': fields.Integer(required=True, description='The year of the film'),
    'total_watches': fields.Integer(required=True, description='Total watches of the film'),
    'ref': fields.String(required=True, description='Reference URL for for the film'),
    'img_reg': fields.String(required=True, description='Image Reference URL for the film'),
    'genres': fields.List(fields.String, description='List of genres')
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
        return FilmService.create_film(data['title'], data['year'], data['total_watches'], data['ref'], data['img_reg'], data['genres']), 201

@api.route('/<int:id>')
@api.response(404, 'Film not found')
@api.param('id', 'The film identifier')
class Film(Resource):
    @api.marshal_with(film_model)
    def get(self, id):
        """Fetch a film given its identifier"""
        film = FilmService.get_film_by_id(id)
        if film:
            return film
        api.abort(404)

    @api.expect(film_model)
    @api.marshal_with(film_model)
    def put(self, id):
        """Update a film given its identifier"""
        data = request.json
        return FilmService.update_film(id, data.get('title'), data.get('year'), data.get('total_watches'), data.get('ref'), data.get('img_reg'), data.get('genres'))

    @api.response(204, 'Film deleted')
    def delete(self, id):
        """Delete a film given its identifier"""
        FilmService.delete_film(id)
        return '', 204