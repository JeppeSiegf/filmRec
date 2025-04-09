from datetime import datetime

from sqlalchemy import desc, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased

from api import db
from api.models import Crew, Role
from api.models.credit import Credit
from api.models.film import Film
from api.models.genre import Genre, film_genre
from api.models.language import film_language, Language


class FilmRepository:
    # CRUD
    @staticmethod
    def get_all_films():

        try:
            return Film.query.filter().all()
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return []

    @staticmethod
    def get_newest_film():

        result = Film.query.order_by(Film.last_update.desc(), Film.id.desc()).first()
        return result

    @staticmethod
    def get_film_by_ref_without_crew(page_ref):

        result = Film.query.filter_by(page_ref=page_ref).first()

        return result

    @staticmethod
    def get_film_by_ref_with_crew(page_ref: str):
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
    def get_films_by_refs_with_crew(page_refs):

        try:
            if not page_refs:  # Handle empty input list
                return []

            # Aliases for clarity
            role_alias = aliased(Role)
            credit_alias = aliased(Credit)
            crew_alias = aliased(Crew)

            # Query to fetch films matching the input page_refs
            films_query = (
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
                .filter(Film.page_ref.in_(page_refs))  # Filter by the input list
                .group_by(Film.page_ref)  # Group by film to aggregate crew
            )

            # Fetch results (list of tuples: (Film, crew_members))
            results = films_query.all()

            # Process each film to attach crew_members
            films = []
            for film, crew_members in results:
                film.crew_members = crew_members if crew_members else []
                films.append(film)

            return films

        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return []  # Return empty list on error

    @staticmethod
    def get_films_by_refs_without_crew(page_refs: list[str]):
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

    @staticmethod
    def update_film(film_id, updates):
        """
        Update a film using the current Flask request context session.
        This version updates all columns provided in the updates dictionary,
        except for the film's primary key and page_ref.
        """
        try:
            # Get the film by its page_ref
            film = Film.query.filter_by(page_ref=film_id).first()
            if not film:
                print(f"Film {film_id} not found.")
                return None

            # If updates is an object, convert to a dictionary
            if hasattr(updates, '__dict__'):
                updates = {k: v for k, v in vars(updates).items() if not k.startswith('_')}

            # Define fields to skip from updates (e.g., primary key and immutable fields)
            skip_fields = {"page_ref", "id", "genres", "languages", "crew", "cast"}

            # Loop through updates and update film attributes if they exist on the film model
            for key, value in updates.items():
                if key in skip_fields:
                    continue
                if hasattr(film, key):
                    setattr(film, key, value)
                    # Optionally, use flag_modified if you need to force the change tracking:
                    # flag_modified(film, key)

            # Always update the last_update timestamp
            film.last_update = datetime.utcnow()


            # Commit all changes at once
            db.session.commit()
            db.session.refresh(film)
            return film

        except Exception as e:
            print(f"Error updating film {film_id}: {e}")
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
    def _validate_film(film):
        required_fields = ['title', 'page_ref', 'last_update']
        for field in required_fields:
            if getattr(film, field, None) is None:
                raise ValueError(f"Film is missing required field: {field}")

    @staticmethod
    def update_series_ids(series, film_page_refs):
        Film.query.filter(Film.page_ref.in_(film_page_refs)).update(
            {Film.series_id: series.id},
            synchronize_session=False
        )
        db.session.commit()


    @staticmethod
    def bulk_insert_ignore_conflict(model, unique_field: str, values: list[str]) -> None:

        if not values:
            return
        insert_data = [{unique_field: val} for val in values]
        try:
            stmt = insert(model).values(insert_data)
            stmt = stmt.on_conflict_do_nothing(index_elements=[unique_field])
            db.session.execute(stmt)
            db.session.flush()  # flush so that any new rows get assigned an ID
        except Exception as e:
            db.session.rollback()
            print(f"Error during bulk insert on {model.__name__}: {e}")
            raise

    @staticmethod
    def insert_association_entries(association_table, entries: list[dict]) -> None:

        if not entries:
            return
        try:
            stmt = insert(association_table).values(entries)
            stmt = stmt.on_conflict_do_nothing()  # Skips duplicates
            db.session.execute(stmt)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error inserting association entries: {e}")
            raise

    @staticmethod
    def get_languages(language_names):

        return Language.query.filter(Language.language.in_(language_names)).all()

    @staticmethod
    def get_genres(genre_names):

        return Genre.query.filter(Genre.genre.in_(genre_names)).all()




