from dataCollectors.film_detail_collector import FilmDetailCollector
from dataCollectors.test.fixtures import FILM_FULL_DATA
import pytest

from dataCollectors.test.test_base import GenericCollectorTest


@pytest.mark.asyncio
@pytest.mark.parametrize("film_ref", list(FILM_FULL_DATA.keys()))
class TestFilmDetailCollector(GenericCollectorTest):
    COLLECTOR_CLASS = FilmDetailCollector
    DATASET = FILM_FULL_DATA

    @pytest.fixture(autouse=True)
    async def setup(self, film_ref):
        """Create collector for this film_ref"""
        await self.setup_collector_for(film_ref)

    def test_page_ref(self):
        self._assert_equal("page_ref")

    def test_title(self):
        self._assert_equal("title")

    def test_title_original(self):
        self._assert_equal("title_original")

    def test_description(self):
        self._assert_equal("description")

    def test_image_refs(self):
        self._assert_equal("image_ref")
        self._assert_equal("image_ref_large")

    def test_banner_ref(self):
        self._assert_equal("banner_ref")

    def test_release_year(self):
        self._assert_equal("release_year")

    def test_runtime(self):
        self._assert_equal("runtime")

    def test_total_watches(self):
        self._assert_gte("total_watches")  # maybe use gte here if actual can grow

    def test_genres(self):
        self._assert_equal("genres")

    def test_languages(self):
        self._assert_equal("languages")

    def test_series_id(self):
        self._assert_equal("series_id")

    def test_crew(self):
        self._assert_equal("crew")

    def test_cast(self):
        self._assert_equal("cast")

    def test_imdb_ref(self):
        self._assert_equal("imdb_ref")

    def test_avg_rating(self):
        self._assert_gte("avg_rating")  # ratings can be float, may allow >=
