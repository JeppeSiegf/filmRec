from api import db
from api.models.language import Language, Film_Language
from api.repositories.film_repository import FilmRepository
from api.repositories.language_repository import LanguageRepository
from api.repositories.utils.bulk_persisting import BulkPersistence


class LanguageService:

    def __init__(self):
        self.repo = LanguageRepository()

    def bulk_update_film_languages(self, film_language_pairs: list[tuple[str, list[dict]]]) -> list[dict]:
        """
        Accepts a list of (film_ref, languages) tuples and updates film-language associations in bulk.
        Assumes all film_refs are valid and exist in the database.
        """
        try:
            # Validate and collect all unique language names
            unique_language_names = set()
            for _, languages in film_language_pairs:
                if not isinstance(languages, list) or not all(
                        isinstance(lang, dict) and "name" in lang and "is_primary" in lang for lang in languages
                ):
                    raise ValueError(
                        "Invalid languages format. Expected list of dicts with 'name' and 'is_primary' keys."
                    )
                unique_language_names.update(lang["name"] for lang in languages)

            language_records = [{'language': name} for name in unique_language_names]

            # Bulk insert languages (ignore duplicates)
            self.repo.insert(list(language_records))

            # Get language objects and build name-to-id map
            language_objs = self.repo.get_by_languages_name(unique_language_names)
            lang_map = {lang.language: lang.id for lang in language_objs}

            # Build bulk association entries
            association_entries = []
            for film_ref, languages in film_language_pairs:
                for lang in languages:
                    lang_id = lang_map.get(lang["name"])
                    if lang_id:
                        association_entries.append({
                            "film_id": film_ref,
                            "language_id": lang_id,
                            "is_primary": lang["is_primary"]
                        })

            # Insert into association table with ON CONFLICT DO NOTHING
            self.repo.upsert(association_entries,
                             self.repo.assoc_table,
                             self.repo.assoc_conflicts_columns,
                             self.repo.assoc_update_columns)

            return association_entries
        except Exception as e:
            db.session.rollback()
            print(f"Error in bulk language update: {e}")
            raise
