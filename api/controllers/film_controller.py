import asyncio
from datetime import datetime
from flask_restx import Namespace, Resource, fields
from flask import request
from api.controllers.genre_controller import Genre
from api.dataCollectors.film_detail_collector import FilmDetailCollector
from api.services.film_service import FilmService
from api.models.film import Film

api = Namespace('films', description='Film operations')

#  Film model schema
film_model = api.model('Film', {
    'page_ref': fields.String(required=True, description='Reference URL for the film'),
    'image_ref': fields.String(description='Image Reference URL for the film'),
    'image_ref_large': fields.String(description='Higher quality image ref'),
    'title': fields.String(description='The film title'),
    'release_year': fields.Integer(description='Year of release'),
    'genres' : fields.List(fields.String, description='List of genres'),
    'directors': fields.List(fields.String, description='List of director names'),

})

@api.route('/')
class FilmList(Resource):
    @api.marshal_list_with(film_model)
    @api.param('search_query', 'The search query to filter films by title or other attributes')
    def get(self):
        """List all films or search for films"""
        search_query = request.args.get('search_query', '')  # Retrieve the query parameter
        films = FilmService.search_films(search_query)  # Call the service method synchronously
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
        created_film = FilmService.create_film(film)  # Call the service method synchronously
        return created_film, 201

@api.route('/<string:page_ref>')
@api.response(404, 'Film not found')
@api.param('page_ref', 'The film reference')
class FilmResource(Resource):
    @api.marshal_with(film_model)
    def get(self, page_ref):
        """Fetch a film given its reference"""
        film = FilmService.get_film_by_page_ref(page_ref)  # Call the service method synchronously
        if film:
            return film
        api.abort(404, "Film not found")

    @api.expect(film_model)
    @api.marshal_with(film_model)
    def put(self, page_ref):
        """Update a film given its reference."""
        updated_data = request.json  # Get the updated data from the request

        try:
            updated_film = FilmService.update_film(page_ref)
            return {
                "message": "Film updated successfully",
                "film": {
                    "page_ref": updated_film.page_ref,
                    "title": updated_film.title,
                    "image_ref": updated_film.image_ref,
                    "total_watches": updated_film.total_watches,
                    "release_year": updated_film.release_year,
                    "last_update": updated_film.last_update,
                    "genres": [genre.genre for genre in updated_film.genres]
                }
            }, 200
        except ValueError as e:
            return {"message": str(e)}, 404
