import abc

from dataCollectors.utils.page_parser import PageParser
from dataCollectors.utils.session_manager import SessionManager


class PageCollector(PageParser, SessionManager):

    def __init__(self, film_ref):

        self. url = f'https://letterboxd.com/film/{film_ref}/'
        self.data = {}

    @abc.abstractmethod
    async def fetch_page(self, session = None):
        pass

    @abc.abstractmethod
    async def extract_details(self):
        pass
