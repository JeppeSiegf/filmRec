import asyncio
from .. import db, create_app
from dataCollectors.theme_collector import ThemeCollector  # adjust import path if needed
from ..services.film_service import FilmService


class ThemeService:
    def __init__(self, repo):
        self.repo = repo
      

    def update_film_themes(self, film_theme_pairs: list[tuple[str, list[dict] | list[str]]]):
        """
        film_theme_pairs: [(film_ref, [ {'name':..., 'slug':...}, ... ])] or [(film_ref, ['slug', ...])]
        Converts incoming collector data to DB format and upserts themes and associations.
        """
        try:
            # 1) collect unique slugs and map slug->name
            unique_slugs = set()
            slug_to_name = {}
            for film_id, themes in film_theme_pairs:
                if not themes:
                    continue
                for t in themes:
                    if isinstance(t, dict):
                        slug = str(t.get("slug") or t.get("theme_ref") or "").strip().lower()
                        name = t.get("name") or t.get("theme_name") or slug
                    else:
                        slug = str(t).strip().lower()
                        name = slug
                    if not slug:
                        continue
                    unique_slugs.add(slug)
                    slug_to_name.setdefault(slug, name)

            if not unique_slugs:
                return []

            # 2) prepare theme records for upsert (theme_ref unique)
            theme_records = [{'theme_ref': s, 'theme_name': slug_to_name.get(s, s)} for s in unique_slugs]

            # 3) upsert themes
            self.repo.insert(theme_records)  # expects to do upsert / on conflict

            # 4) get themes from DB and build slug -> id map
            theme_objs = self.repo.get_all_themes() or []
            theme_lookup = {}
            for t in theme_objs:
                ref = (getattr(t, "theme_ref", "") or "").strip().lower()
                if ref:
                    theme_lookup[ref] = t.id

            # 5) build association entries (film_id, theme_id)
            assoc_entries = []
            for film_id, themes in film_theme_pairs:
                if not themes:
                    continue
                for t in themes:
                    slug = (t.get("slug") if isinstance(t, dict) else t) if t else None
                    if not slug:
                        continue
                    slug = str(slug).strip().lower()
                    theme_id = theme_lookup.get(slug)
                    if theme_id:
                        assoc_entries.append({'film_id': film_id, 'theme_id': theme_id})

            # 6) bulk insert associations (skip duplicates)
            if assoc_entries:
                self.repo.insert(
                    assoc_entries,
                    self.repo.assoc_table,
                    self.repo.assoc_conflicts_columns
                )

            return assoc_entries
        except Exception as e:
            db.session.rollback()
            print(f"Error in bulk theme update: {e}")
            raise

    async def scrape_themes(self, refs: list[str]):
        """
        Scrape themes for given film refs and update DB (in-place conversion).
        Returns number of films processed.
        """
        await ThemeCollector.enable_shared_session()
        sem = asyncio.Semaphore(50)
        tasks = [self._fetch_and_extract(ref, sem) for ref in refs]
        collectors = await asyncio.gather(*tasks, return_exceptions=False)
        await ThemeCollector.disable_shared_session()

        # convert collectors -> film_theme_pairs expected by update_film_themes
        pairs = []
        for c in collectors:
            if not c:
                continue
            # c.themes expected as list of {'name':..., 'slug':...}
            themes = []
            for t in getattr(c, "themes", []) or []:
                name = t.get("name") or t.get("theme_name")
                slug = t.get("slug") or t.get("theme_ref")
                if slug:
                    themes.append({'name': name or slug, 'slug': slug})
            if themes:
                pairs.append((c.film_slug, themes))

        if not pairs:
            return 0

        # reuse existing method (does upserts and associations)
        self.update_film_themes(pairs)
        return len(pairs)

    async def _fetch_and_extract(self, film_ref: str, sem: asyncio.Semaphore) -> ThemeCollector | None:
        async with sem:
            try:
                collector = ThemeCollector(film_ref)
                await collector.fetch_page()
                await collector.extract_themes()
                # collector.themes should now be a list of {'name','slug'} dicts
                print(f"[SCRAPED] {film_ref} -> {collector.themes}")
                return collector
            except Exception as e:
                print(f"[ERROR] Failed to collect for {film_ref}: {e}")
                return None


# --- quick test main ---
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        import asyncio
        from api import ThemeRepository

        repo = ThemeRepository()
        svc = ThemeService(repo)
        filmsvc = FilmService()

        films = filmsvc.get_all_films()
        refs = [f.page_ref for f in films]

        batch_size = 1000
        total_refs = len(refs)

        total_processed = 0
        for start in range(0, total_refs, batch_size):
            end = start + batch_size
            batch = refs[start:end]
            print(f"Processing films {start + 1} to {min(end, total_refs)}...")

            count = asyncio.run(svc.scrape_themes(batch))
            total_processed += count

        print(f"Processed {total_processed} films in total.")

