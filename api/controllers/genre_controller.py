from flask_restx import Namespace, Resource, fields
from api.services.genre_service import GenreService

api = Namespace('genres', description='Genre operations')

genre_model = api.model('Genre', {
    'id': fields.Integer(readonly=True, description='unique identifier'),
    'genre': fields.String(required=True, description='genre name')
})


@api.route('/')
class GenreList(Resource):
    @api.marshal_list_with(genre_model)
    def get(self):
        return GenreService.get_all_genres()


class Genre(Resource):
    @api.marshal_with(genre_model)
    def get(self, id):
        """Fetch a genre given its identifier"""
        genre = GenreService.get_genre_by_id(id)
        if genre:
            return genre
        api.abort(404)
