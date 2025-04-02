import traceback
from datetime import datetime

from sqlalchemy import desc, func, update, inspect, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased, joinedload
from sqlalchemy.orm.attributes import set_attribute, flag_modified

from api import db
from api.models import Crew, Role, role
from api.models.credit import Credit
from api.models.film import Film
from api.models.genre import Genre
from api.models.language import film_language, Language


class FilmRepository:
    # CRUD
    @staticmethod
    def get_all_films():
        #TODO remove the desc part
        try:
            return Film.query.filter(Film.description.is_(None)).all()
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return []

    @staticmethod
    def get_newest_film():

        result = Film.query.order_by(Film.last_update.desc(), Film.id.desc()).first()
        return result

    @staticmethod
    def filter_invalid_refs(film_refs):

        films = Film.query.filter(Film.page_ref.in_(film_refs)).all()
        return {f.page_ref for f in films}

    @staticmethod
    def get_film_by_ref(page_ref: str):
        try:
            # Aliases for clarity
            role_alias = aliased(Role)
            credit_alias = aliased(Credit)
            crew_alias = aliased(Crew)

            # Build a query to fetch the film with its associated crew members (with roles)
            film_query = (
                db.session.query(
                    Film,
                    func.array_agg(
                        func.json_build_object(
                            'page_ref', crew_alias.page_ref,
                            'name', crew_alias.name,
                            'role', role_alias.role
                        )
                    ).label("crew_members")
                )
                .outerjoin(credit_alias, credit_alias.film_id == Film.page_ref)
                .outerjoin(role_alias, role_alias.id == credit_alias.role_id)
                .outerjoin(crew_alias, crew_alias.page_ref == credit_alias.crew_id)
                .filter(Film.page_ref == page_ref)  # Exact match on page_ref
                .group_by(Film.page_ref)
            )

            # Fetch the film (should be at most one result)
            result = film_query.first()
            if result:
                film, crew_members = result
                # Ensure that the film has a crew_members attribute (empty list if none found)
                film.crew_members = crew_members if crew_members else []
                return film
            else:
                return None

        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return None

    @staticmethod
    def get_films_by_refs(page_refs: list[str]):
        if not page_refs:
            return []

        films = Film.query.filter(Film.page_ref.in_(page_refs)).order_by(desc(Film.total_watches)).all()
        return films

    @staticmethod
    def search_films(query: str, limit: int = 15):
        try:
            # Query films directly from the Film table based on the title search
            films_query = (
                db.session.query(Film)
                .filter(Film.title.ilike(f"%{query}%"))  # Filter films by title
                .order_by(
                    func.lower(Film.title).like(f"{query.lower()}%").desc(),  # Prioritize the exact match
                    desc(Film.total_watches)  # Order by total_watches
                )
                .limit(limit)  # Limit the number of results
            )

            # Execute and fetch results
            films = films_query.all()
            return films

        except Exception as e:
            print(f"Error in search_films2: {e}")
            return []

    def search_films_by_director(director_ref: str):
        try:
            # Aliases
            director_role = aliased(Role)
            credit = aliased(Credit)
            crew = aliased(Crew)

            # Query films and fetch director names inline as tuples (page_ref, name)
            films_query = (
                db.session.query(
                    Film,
                    func.array_agg(func.json_build_object(
                        'page_ref', crew.page_ref,
                        'name', crew.name
                    )).filter(director_role.role == "director").label("directors")
                )
                .outerjoin(credit, credit.film_id == Film.page_ref)
                .outerjoin(director_role, director_role.id == credit.role_id)
                .outerjoin(crew, crew.page_ref == credit.crew_id)

                .group_by(Film.page_ref)
                .order_by(desc(Film.total_watches))  # You can add other ordering logic as needed

            )

            # Fetch results
            results = films_query.all()

            # Assign directors to each film object properly
            for film, directors in results:
                film.directors = directors if directors else []  # Ensure no None values

            return [film for film, _ in results]

        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return []

    @staticmethod
    def create_film(film):

        FilmRepository._validate_film(film)

        try:

            db.session.add(film)
            db.session.commit()
            return film
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error: {e}")
            return None


    @staticmethod
    def bulk_insert_films(film_data):

        if not film_data:
            print("No film data provided.")
            return []

        stmt = insert(Film).values(film_data)
        stmt = stmt.on_conflict_do_nothing(index_elements=["page_ref"])

        try:
            db.session.execute(stmt)
            db.session.commit()
            print("Inserted films (duplicates were skipped).")
            return film_data
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error during bulk insert: {e}")
            return []

    from sqlalchemy.orm.attributes import set_attribute
    from sqlalchemy import inspect, text
    from datetime import datetime
    from sqlalchemy.exc import SQLAlchemyError

    from sqlalchemy.orm.attributes import flag_modified
    from sqlalchemy import inspect
    from datetime import datetime
    from sqlalchemy.exc import SQLAlchemyError

    from sqlalchemy.orm.attributes import flag_modified
    from datetime import datetime
    from sqlalchemy.exc import SQLAlchemyError
    import traceback


    @staticmethod
    def update_film(film_id, updates):
        """
        Update a film using the current Flask request context session.
        """
        try:
            # Get the film
            film = Film.query.filter_by(page_ref=film_id).first()

            if not film:
                print(f"Film {film_id} not found.")
                return None

            # Make sure film is attached to the current session
            db.session.add(film)

            # Process updates
            if not updates:
                print(f"No updates provided for {film_id}")
                # Update timestamp even with no updates
                film.last_update = datetime.utcnow()
                flag_modified(film, 'last_update')
                db.session.commit()
                return film

            # Convert to dict if needed
            if hasattr(updates, '__dict__'):
                updates = {k: v for k, v in vars(updates).items() if not k.startswith('_')}

            allowed_columns = {
                'title', 'title_original', 'description', 'image_ref',
                'image_ref_large', 'release_year', 'runtime', 'total_watches'
            }

            content_modified = False
            for col in allowed_columns:
                if col in updates:
                    old_value = getattr(film, col)
                    new_value = updates[col]

                    # Only update if values are different
                    if old_value != new_value:
                        print(f"Updating {col}: {old_value} -> {new_value}")
                        setattr(film, col, new_value)
                        flag_modified(film, col)
                        content_modified = True

            # Always update the timestamp, regardless of content changes
            film.last_update = datetime.utcnow()
            flag_modified(film, 'last_update')

            # Commit changes
            print("Committing changes...")
            db.session.commit()

            if content_modified:
                print(f"Film content updated for {film_id}")
            else:
                print(f"Only timestamp updated for {film_id}")

            # Refresh the film to ensure it's up-to-date
            db.session.refresh(film)

            return film

        except SQLAlchemyError as e:
            print(f"Database error during update: {e}")
            traceback.print_exc()
            db.session.rollback()
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            traceback.print_exc()
            db.session.rollback()
            return None
    @staticmethod
    def delete_film(page_ref):
        try:
            film = Film.query.filter_by(page_ref=page_ref).first()
            if film:
                db.session.delete(film)
                db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error: {e}")

    @staticmethod
    def update_film_genres(existing_film, genres):
        try:
            # Ensure the film is attached to the current session.
            film = db.session.merge(existing_film)

            # Fetch existing genres from the database.
            existing_genres = {g.genre: g for g in Genre.query.filter(Genre.genre.in_(genres)).all()}
            new_genres = []

            for genre_title in genres:
                if genre_title in existing_genres:
                    new_genres.append(existing_genres[genre_title])
                else:
                    new_genre = Genre(genre=genre_title)
                    db.session.add(new_genre)
                    new_genres.append(new_genre)

            # Update the film's genres and commit.
            film.genres = new_genres
            db.session.commit()
            return new_genres

        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error: {e}")
            return None

    @staticmethod
    def update_film_languages(existing_film, languages):
        try:
            # Validate input structure
            if not isinstance(languages, list) or not all(
                    isinstance(lang, dict) and "name" in lang and "is_primary" in lang
                    for lang in languages
            ):
                raise ValueError(
                    "Invalid languages format. Expected list of dictionaries with 'name' and 'is_primary' keys."
                )

            # Extract language names from the list of dictionaries
            language_names = [lang["name"] for lang in languages]

            # Query existing languages by name
            existing_languages = {l.language: l for l in
                                  Language.query.filter(Language.language.in_(language_names)).all()}
            new_languages = []

            # Iterate over the list of language dictionaries
            for lang_dict in languages:
                language_title = lang_dict["name"]
                is_primary = lang_dict["is_primary"]

                if language_title in existing_languages:
                    language_obj = existing_languages[language_title]
                else:
                    language_obj = Language(language=language_title)
                    db.session.add(language_obj)

                new_languages.append({'language': language_obj, 'is_primary': is_primary})

            # Clear existing relationships
            db.session.execute(
                film_language.delete().where(film_language.c.film_id == existing_film.page_ref)
            )

            # Insert new relationships
            for lang in new_languages:
                db.session.execute(
                    film_language.insert().values(
                        film_id=existing_film.page_ref,
                        language_id=lang['language'].id,
                        is_primary=lang['is_primary']
                    )
                )

            db.session.commit()
            return new_languages
        except Exception as e:
            db.session.rollback()
            print(f"Error updating languages: {e}")
            raise

    @staticmethod
    def _validate_film(film):
        required_fields = ['title', 'page_ref', 'last_update']
        for field in required_fields:
            if getattr(film, field, None) is None:
                raise ValueError(f"Film is missing required field: {field}")


