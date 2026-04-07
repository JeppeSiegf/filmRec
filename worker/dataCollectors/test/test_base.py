import pytest
import logging

logger = logging.getLogger(__name__)

class GenericCollectorTest:
    """
    Generic test class for any collector.
    Subclasses must define:
      - COLLECTOR_CLASS: the collector class to test
      - DATASET: dict of {film_ref: expected_data}
    """

    COLLECTOR_CLASS = None
    DATASET = {}

    async def setup_collector_for(self, film_ref):
        """Helper to create a collector for a specific film_ref"""
        collector = self.COLLECTOR_CLASS(film_ref)
        await collector.fetch_page()
        await collector.extract_details()
        self.collector = collector
        self.data = collector.get_data()
        self.expected = self.DATASET[film_ref]
        self.film_ref = film_ref

    def _assert_equal(self, key):
        expected = self.expected[key]
        actual = self.data.get(key)
        if expected != actual:
            logger.error(
                "Mismatch on '%s' for film '%s':\nExpected: %r\nActual:   %r",
                key, self.film_ref, expected, actual
            )
        assert actual == expected, f"Attribute '{key}' mismatch for film '{self.film_ref}'"

    def _assert_gte(self, key):
        expected = self.expected[key]
        actual = self.data.get(key)
        if actual < expected:
            logger.error(
                "Expected '%s' >= %r for film '%s', got %r",
                key, expected, self.film_ref, actual
            )
        assert actual >= expected, f"Attribute '{key}' mismatch for film '{self.film_ref}'"
