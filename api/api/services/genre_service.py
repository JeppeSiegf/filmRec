from .. import db
from ..repositories.genre_repository import GenreRepository


class GenreService:

    def __init__(self):
        self.repo = GenreRepository()

    def get_all_genres(self):
        return self.repo.get_all_genres()

    def get_genre_by_id(self, genre_id):
        return self.get_genre_by_id(genre_id)

    def update_film_genres(self, film_genre_pairs: list[tuple[str, list[str]]]):

        try:
            # Flatten all genre names into one set to bulk insert
            unique_genres = set()
            for _, genres in film_genre_pairs:
                unique_genres.update(genres)

            genre_records = [{'genre': g} for g in unique_genres]

            # Insert all genres, skipping existing ones
            self.repo.insert(list(genre_records))

            # Map genre name to Genre object
            genre_objs = self.repo.get_all_genres()
            genre_lookup = {g.genre: g.id for g in genre_objs}

            # Build bulk association entries
            association_entries = []
            for film_ref, genres in film_genre_pairs:
                for genre in genres:
                    genre_id = genre_lookup.get(genre)
                    if genre_id:
                        association_entries.append({'film_id': film_ref, 'genre_id': genre_id})

            # Insert associations, skipping duplicates
            self.repo.insert(association_entries,
                             self.repo.assoc_table,
                             self.repo.assoc_conflicts_columns
                             )

            return association_entries
        except Exception as e:
            db.session.rollback()
            print(f"Error in bulk genre update: {e}")
            raise
