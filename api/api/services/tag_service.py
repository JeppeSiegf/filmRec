import asyncio
from .. import db, create_app
from dataCollectors.theme_collector import ThemeCollector  # we still use ThemeCollector as requested


class TagService:
    def __init__(self, repo):
        self.repo = repo

    def update_film_tags(self, film_tag_pairs: list[tuple[str, list[dict] | list[str]]]):
        """
        film_tag_pairs: [(film_ref, [ {'name':..., 'slug':...}, ... ])] or [(film_ref, ['slug', ...])]
        Converts incoming collector data to DB format and upserts tags and associations.
        Mirrors the ThemeService flow but operates on tags while reusing ThemeCollector for extraction.
        """
        try:
            # 1) collect unique slugs and map slug->name
            unique_slugs = set()
            slug_to_name = {}
            for film_id, tags in film_tag_pairs:
                if not tags:
                    continue
                for t in tags:
                    if isinstance(t, dict):
                        slug = str(t.get("slug") or t.get("tag_ref") or "").strip().lower()
                        name = t.get("name") or t.get("tag_name") or slug
                    else:
                        slug = str(t).strip().lower()
                        name = slug
                    if not slug:
                        continue
                    unique_slugs.add(slug)
                    slug_to_name.setdefault(slug, name)

            if not unique_slugs:
                return []

            # 2) prepare tag records for upsert (tag_ref unique)
            tag_records = [{'tag_ref': s, 'tag_name': slug_to_name.get(s, s)} for s in unique_slugs]

            # 3) upsert tags
            # repo.insert(...) is expected to perform upsert / on conflict behavior
            self.repo.insert(tag_records)

            # 4) get tags from DB and build slug -> id map
            tag_objs = self.repo.get_all_tags() or []
            tag_lookup = {}
            for t in tag_objs:
                ref = (getattr(t, "tag_ref", "") or "").strip().lower()
                if ref:
                    tag_lookup[ref] = t.id

            # 5) build association entries (film_id, tag_id)
            assoc_entries = []
            for film_id, tags in film_tag_pairs:
                if not tags:
                    continue
                for t in tags:
                    slug = (t.get("slug") if isinstance(t, dict) else t) if t else None
                    if not slug:
                        continue
                    slug = str(slug).strip().lower()
                    tag_id = tag_lookup.get(slug)
                    if tag_id:
                        assoc_entries.append({'film_id': film_id, 'tag_id': tag_id})

            # 6) bulk insert associations (skip duplicates)
            if assoc_entries:
                # repo.insert accepts (records, assoc_table, conflict_columns) similar to ThemeService
                self.repo.insert(
                    assoc_entries,
                    self.repo.assoc_table,
                    self.repo.assoc_conflicts_columns
                )

            return assoc_entries
        except Exception as e:
            db.session.rollback()
            print(f"Error in bulk tag update: {e}")
            raise

    async def scrape_tags(self, refs: list[str], nanogenre: bool = True):
        """
        Scrape tags for given film refs and update DB (in-place conversion).
        Uses ThemeCollector to fetch/extract and then maps extracted themes -> tags.
        If nanogenre=True, ThemeCollector will hit the nanogenres page (used for tag-like data).
        Returns number of films processed.
        """
        await ThemeCollector.enable_shared_session()
        sem = asyncio.Semaphore(50)
        tasks = [self._fetch_and_extract(ref, sem, ) for ref in refs]
        collectors = await asyncio.gather(*tasks, return_exceptions=False)
        await ThemeCollector.disable_shared_session()

        # convert collectors -> film_tag_pairs expected by update_film_tags
        pairs = []
        for c in collectors:
            if not c:
                continue
            # c.themes expected as list of {'name':..., 'slug':...}
            tags = []
            for t in getattr(c, "themes", []) or []:
                name = t.get("name") or t.get("theme_name")
                slug = t.get("slug") or t.get("theme_ref")
                if slug:
                    # map theme -> tag structure (we intentionally reuse fields 'name' and 'slug')
                    tags.append({'name': name or slug, 'slug': slug})
            if tags:
                pairs.append((c.film_slug, tags))

        if not pairs:
            return 0

        # reuse existing method (does upserts and associations)
        self.update_film_tags(pairs)
        return len(pairs)

    async def _fetch_and_extract(self, film_ref: str, sem: asyncio.Semaphore) -> ThemeCollector | None:
        async with sem:
            try:
                collector = ThemeCollector(film_ref, True)
                await collector.fetch_page()
                await collector.extract_themes()
                # collector.themes should now be a list of {'name','slug'} dicts
                print(f"[SCRAPED for TAGS] {film_ref} -> {collector.themes}")
                return collector
            except Exception as e:
                print(f"[ERROR] Failed to collect for {film_ref}: {e}")
                return None


# --- quick test main (kept for convenience) ---
if __name__ == "__main__":
    # This example is intended to be run inside your Flask app context so SQLAlchemy/DB are available.
    app = create_app()
    with app.app_context():
        import asyncio
        from api import TagRepository
        from api import FilmService

        repo = TagRepository()
        svc = TagService(repo)
        filmsvc = FilmService()

        films = filmsvc.get_all_films()
        refs = [f.page_ref for f in films]

        # smaller batch for local testing
        batch_size = 500
        total_refs = len(refs)

        total_processed = 0
        for start in range(0, total_refs, batch_size):
            end = start + batch_size
            batch = refs[start:end]
            print(f"Processing films {start + 1} to {min(end, total_refs)}... (nanogenre tags)")

            count = asyncio.run(svc.scrape_tags(batch, nanogenre=True))
            total_processed += count

        print(f"Processed {total_processed} films in total.")
