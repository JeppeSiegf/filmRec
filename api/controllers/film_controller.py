import asyncio
from datetime import datetime
from flask_restx import Namespace, Resource, fields
from flask import request

from api.controllers.api_models import film_model, film_model_simple
from api.controllers.genre_controller import Genre
from api.dataCollectors.film_detail_collector import FilmDetailCollector
from api.services.film_service import FilmService
from api.models.film import Film

api = Namespace('films', description='Film operations')


#  Film model schema


@api.route('/')
class FilmList(Resource):
    @api.marshal_list_with(film_model_simple)
    @api.param('search_query', 'The search query to filter films by title or other attributes')
    def get(self):
        """List all films or search for films"""
        search_query = request.args.get('search_query', '')  # Retrieve the query parameter
        films = FilmService.search_films(search_query)  # Call the service method synchronously
        if films:
            return films
        api.abort(404, "No matching films found")

    @api.expect([film_model_simple], validate=True)
    @api.marshal_with(film_model_simple, code=201)
    def post(self):
        """Bulk create or update films."""
        films_data = request.json  # Expecting a list of film objects

        if not isinstance(films_data, list) or not films_data:
            return {"message": "Invalid input. Expected a non-empty list of films."}, 400

        try:
            # Call your service method to bulk upsert films
            result = FilmService.create_multiple_films(films_data)

            return result, 201

        except Exception as e:
            return {"message": f"Error processing films: {str(e)}"}, 500


@api.route('/by')
class FilmByCrewMember(Resource):
    @api.marshal_with(film_model)
    @api.param('director_ref', 'The reference of the director to filter films by')
    def get(self):
        """"Fetch films by director reference"""
        dir_ref = request.args.get('director_ref', '')
        film = FilmService.get_films_by_crew_member(dir_ref)
        if film:
            return film
        api.abort(404, "Film not found")

@api.route('/latest')
@api.response(404, 'Film not found')
class FilmResource(Resource):
    @api.marshal_with(film_model_simple)
    def get(self):
        """Fetch a film given its reference"""
        film = FilmService.get_newest_film()  # Call the service method synchronously
        if film:
            return film
        api.abort(404, "Film not found")
@api.route('/<string:page_ref>')
@api.response(404, 'Film not found')
@api.param('page_ref', 'The film reference')
class FilmResource(Resource):
    @api.marshal_with(film_model)
    def get(self, page_ref):
        """Fetch a film given its reference"""
        film = FilmService.get_film_by_page_ref(page_ref,True)  # Call the service method synchronously
        if film:
            return film
        api.abort(404, "Film not found")

