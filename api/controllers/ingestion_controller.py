import asyncio

from flask import request
from flask_httpauth import HTTPBasicAuth
from flask_restx import Resource, Namespace
from werkzeug.security import generate_password_hash, check_password_hash

from api.services.ingestion_service import DataIngestionService

# Set up HTTP Basic Auth (only password matters)
auth = HTTPBasicAuth()

# Hardcoded password hash (username is ignored)
VALID_PASSWORD_HASH = generate_password_hash("hello")


@auth.verify_password
def verify_password(username, password):
    # Ignore the username and check only the password
    if check_password_hash(VALID_PASSWORD_HASH, password):
        return True
    return False


# Create a namespace for scraping endpoints
api = Namespace('ingestion', description='Endpoints for manual data ingestion')


@api.route('/films')
class FilmList(Resource):
    @auth.login_required
    @api.param('list_title', 'The title of the film list to scrape')
    @api.param('username', 'The username for the creator of list (ignored)')
    def get(self):
        """Scrape a film list given a list title."""
        list_title = request.args.get('list_title')
        # Even though we ask for a username parameter here, it's not used for auth.
        username = request.args.get('username')
        films = DataIngestionService.ingest_film_list(username, list_title)
        if films:
            return {"message": "Film list scraped successfully", "films": films}, 200
        api.abort(404, "No films found for the given parameters")


@api.route('/films/<string:film_ref>')
class FilmObject(Resource):
    @auth.login_required
    def get(self, film_ref):
        """Scrape details for a single film given its reference."""
        film = asyncio.run(DataIngestionService.ingest_film(film_ref))
        if film:
            return {"message": "Film object scraped successfully", "film": film}, 200
        api.abort(404, "Film not found")


@api.route('/users')
class UserList(Resource):
    @auth.login_required
    @api.param('username', 'The username for which to scrape the user list (ignored)')
    def get(self):
        username = request.args.get('username')
        users_list = DataIngestionService.ingest_user_list(username)
        if users_list:
            return {"message": "User list scraped successfully", "users": users_list}, 200
        api.abort(404, "No users found for the given username")


@api.route('/members')
class MemberList(Resource):
    @auth.login_required
    @api.param('film_ref', 'The film reference for which to scrape the member list')
    def get(self):
        film_ref = request.args.get('film_ref')
        members = DataIngestionService.ingest_member_list(film_ref)
        if members:
            return {"message": "Member list scraped successfully", "members": members}, 200
        api.abort(404, "No members found for the given film reference")


@api.route('/ratings')
class RatingsList(Resource):
    @auth.login_required
    @api.param('username', 'The username for which to scrape the ratings list (ignored)')
    def get(self):
        username = request.args.get('username')
        ratings = DataIngestionService.ingest_ratings_list(username)
        if ratings:
            return {"message": "Ratings list scraped successfully", "ratings": ratings}, 200
        api.abort(404, "No ratings found for the given username")


@api.route('/series')
class SeriesList(Resource):
    @auth.login_required
    def get(self):
        series = DataIngestionService.ingest_series_list()
        if series:
            return {"message": "Series list scraped successfully", "series": series}, 200
        api.abort(404, "No series found")


# Additional endpoint to force authentication on every request (only password is used)
@api.route('/auth-check')
class AuthCheck(Resource):
    @auth.login_required
    def get(self):
        """This endpoint checks that the password is correct.
           It always forces a password check (username is ignored)."""
        return {"message": "Authentication successful"}, 200
