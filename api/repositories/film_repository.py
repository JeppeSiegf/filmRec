from datetime import datetime
from sqlalchemy import desc, func
from scipy.spatial.distance import cosine
from sqlalchemy import func

from api import db
from api.models.film import Film
from api.models.genre import Genre
from api.models.rating import Rating


def generate_page_ref(director_name):
    pass


class FilmRepository:

    # CRUD
    @staticmethod
    def get_all_films():
        return Film.query.all()

    @staticmethod
    def get_film_by_ref(page_ref):
        # Query by page_ref as this is the primary key now
        return Film.query.filter_by(page_ref=page_ref).first()

    @staticmethod
    def search_films(query: str):
        # Query to filter films based on title
        films_query = Film.query.filter(Film.title.ilike(f"%{query}%"))

        films_query = films_query.order_by(desc(getattr(Film, 'total_watches')))

        return films_query.limit(10).all()

    from sqlalchemy.orm import aliased
    @staticmethod
    def get_similar_films(film_id):

        # CTE to find users who rated the film
        rated_users = db.session.query(Rating.user_id).filter(
            Rating.film_id == film_id,
            Rating.liked == True  # Users who rated the film 4 or higher
        ).subquery()

        # CTE to find common users who rated other films
        common_users = (
            db.session.query(
                Rating.film_id,
                func.count(Rating.user_id).label('common_users')
            )
            .filter(Rating.user_id.in_(rated_users))  # Users who rated the target film highly
            .filter(Rating.liked == True)  # Only include films that these users also rated 4 or higher
            .filter(Rating.film_id != film_id)  # Exclude the target film itself
            .group_by(Rating.film_id)
        ).subquery()

        # Final query to get film recommendations based on common users
        recommendations = (
            db.session.query(
                common_users.c.film_id,
                common_users.c.common_users
            )
            .order_by(common_users.c.common_users.desc())  # Rank by number of common users
            .limit(10)  # Limit to top 10 recommendations
            .all()
        )
        print(recommendations)
        # Format recommendations into a list of dictionaries
        recommendations_list = [{'film_id': rec[0], 'common_users': rec[1]} for rec in recommendations]

        return recommendations_list

    @staticmethod
    def get_similar_movies_based_on_distribution(film_id, min_rating=3, limit=10):
        # Step 1: Get users who rated the target movie highly (e.g., >= min_rating)
        users_subquery = (
            db.session.query(Rating.user_id)
            .filter(Rating.film_id == film_id)
            .filter(Rating.rating >= min_rating)
            .subquery()
        )

        # Step 2: Get the rating distribution for the target movie among these users
        target_distribution_query = (
            db.session.query(Rating.rating, func.count(Rating.rating).label('rating_count'))
            .filter(Rating.film_id == film_id)
            .filter(Rating.user_id.in_(users_subquery))
            .group_by(Rating.rating)
            .all()
        )

        total_ratings_target = sum([count for _, count in target_distribution_query])
        target_distribution = {rating: count / total_ratings_target for rating, count in target_distribution_query}

        # Step 3: Get other movies rated by the same users
        other_movies_subquery = (
            db.session.query(Rating.film_id)
            .filter(Rating.user_id.in_(users_subquery))
            .filter(Rating.film_id != film_id)
            .group_by(Rating.film_id)
            .subquery()
        )

        # Step 4: Calculate distribution for these other movies and compare with the target movie
        other_distributions = (
            db.session.query(
                Rating.film_id,
                Rating.rating,
                func.count(Rating.rating).label('rating_count')
            )
            .filter(Rating.film_id.in_(other_movies_subquery))
            .filter(Rating.user_id.in_(users_subquery))
            .group_by(Rating.film_id, Rating.rating)
            .all()
        )

        # Step 5: Calculate distribution similarity (cosine similarity) for each film
        film_distributions = {}
        for film_id, rating, count in other_distributions:
            if film_id not in film_distributions:
                film_distributions[film_id] = {}
            film_distributions[film_id][rating] = count

        similarity_scores = []
        for other_film_id, dist in film_distributions.items():
            total_ratings_other = sum(dist.values())

            if total_ratings_other > 0:
                # Only normalize the distribution if there are ratings
                normalized_distribution = {rating: count / total_ratings_other for rating, count in dist.items()}

                # Perform cosine similarity calculation (or other logic)
                vec1 = [target_distribution.get(rating, 0) for rating in range(1, 6)]
                vec2 = [normalized_distribution.get(rating, 0) for rating in range(1, 6)]

                similarity = 1 - cosine(vec1, vec2)  # Cosine similarity (1 - distance)
                similarity_scores.append((other_film_id, similarity))
            else:
                # Handle the case where there are no ratings (e.g., skip it)
                continue

        # Step 6: Sort by similarity and return top results
        similarity_scores.sort(key=lambda x: x[1], reverse=True)

        # Limit to top N similar movies
        return similarity_scores[:limit]

    @staticmethod
    def create_film(film):
        # film should be an instance of the Film class
        if not isinstance(film, Film):
            raise TypeError("Expected a Film instance.")

        FilmRepository._validate_film(film)

        db.session.add(film)
        db.session.commit()
        return film

    @staticmethod
    def update_film(existing_film, updated_data):
        # Update the film's attributes
        if 'title' in updated_data:
            existing_film.title = updated_data['title']

        if 'image_ref' in updated_data:
            existing_film.image_ref = updated_data['image_ref']

        if 'total_watches' in updated_data:
            existing_film.total_watches = updated_data['total_watches']

        if 'release_year' in updated_data:
            existing_film.release_year = updated_data['release_year']

            # Update last update timestamp
            existing_film.last_update = datetime.now()

        # Commit changes to the database
        db.session.commit()
        return existing_film

    @staticmethod
    def delete_film(page_ref):
        # Query the film by page_ref
        film = Film.query.filter_by(page_ref=page_ref).first()
        if film:
            db.session.delete(film)
            db.session.commit()

        # Additional methods

    # Adds many-to-many relation to db  used both by update and create
    @staticmethod
    def update_film_genres(existing_film, genres):
        # Clear existing genres
        existing_film.genres.clear()

        # Add new genres
        for genre_title in genres:
            # Check if the genre already exists in the database
            genre = Genre.query.filter_by(genre=genre_title).first()

        # If the genre exists, add it to the film's genres
        if genre:
            existing_film.genres.append(genre)
        else:
            # Optionally: Create a new genre if it doesn't exist
            new_genre = Genre(genre=genre_title)
            db.session.add(new_genre)  # Add new genre to the session
            existing_film.genres.append(new_genre)  # Associate the new genre with the film

            # Commit changes to the database
            db.session.commit()

    # Validates non-nullable fields and title (might update schema)
    @staticmethod
    def _validate_film(film):
        required_fields = ['title', 'page_ref', 'last_update']

        for field in required_fields:
            if getattr(film, field, None) is None:
                raise ValueError(f"Film is missing required field: {field}")
