from api.models.genre import Genre


class GenreRepository:

    @staticmethod
    def get_all_genres():
        return Genre.query.all()

    @staticmethod
    def get_genre_by_id(genre_id):
        return Genre.query.get(genre_id)
