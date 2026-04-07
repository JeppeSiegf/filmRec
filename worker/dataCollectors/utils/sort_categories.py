from enum import Enum


class FilmSorting(Enum):
    REVERSE = 'reverse'
    ALPHABETIC = 'name'
    POPULARITY = 'popular'
    RANDOM = 'shuffle'
    LAST_ADDITION = 'added'
    FIRST_ADDITION = 'added-earliest'
    RELEASE_DATE = 'release'
    RELEASE_DATE_REVERSE = 'release-earliest'
    HIGHEST_RATING = 'rating'
    LOWEST_RATING = 'rating_lowest'
    SHORTEST = 'shortest'
    LONGEST = 'longest'

    @staticmethod
    def sort(url, order):

        if isinstance(order, FilmSorting):
            order_value = order.value
        else:
            order_value = order

        url += f'by/{order_value}/'
        return url


class RatingSorting(Enum):
    REVERSE = 'release-earliest'
    ALPHABETIC = 'name'
    POPULARITY = 'popular'
    RANDOM = 'shuffle'
    LAST_ADDITION = 'date'
    FIRST_ADDITION = 'date-earliest'
    HIGHEST_RATING = 'rating'
    LOWEST_RATING = 'rating_lowest'
    SHORTEST = 'shortest'
    LONGEST = 'longest'

    @staticmethod
    def sort(url, order):

        if isinstance(order, RatingSorting):
            order_value = order.value
        else:
            order_value = order

        url += f'by/{order_value}/'
        return url


class UserSorting(Enum):
    ALPHABETIC = 'name'
    WHEN_JOINED = 'whenJoined'
    POPULARITY = 'popular'

    @staticmethod
    def sort(url, order):

        if isinstance(order, UserSorting):
            order_value = order.value
        else:
            order_value = order

        url += f'by/{order_value}/'
        return url


class GenreFilter(Enum):
    ACTION = 'action'
    ADVENTURE = 'adventure'
    ANIMATION = 'animation'
    COMEDY = 'comedy'
    CRIME = 'crime'
    DOCUMENTARY = 'documentary'
    DRAMA = 'drama'
    FAMILY = 'family'
    FANTASY = 'fantasy'
    HISTORY = 'history'
    HORROR = 'horror'
    MUSIC = 'music'
    MYSTERY = 'mystery'
    ROMANCE = 'romance'
    SCIENCE_FICTION = 'science-fiction'
    THRILLER = 'thriller'
    TV_MOVIE = 'tv-movie'
    WAR = 'war'
    WESTERN = 'western'

    @staticmethod
    def filter(url, genres):
        genres = sorted(genres, key=lambda genre: genre.value)

        url += f'genre/{genres[0].value}'
        for genre in genres[1:]:
            url += f'+{genre.value}'
        url += '/'
        return url


class ReleaseDateFilter(Enum):
    DECADE_2020S = '2020s'
    DECADE_2010S = '2010s'
    DECADE_2000S = '2000s'
    DECADE_1990S = '1990s'
    DECADE_1980S = '1980s'
    DECADE_1970S = '1970s'
    DECADE_1960S = '1960s'
    DECADE_1950S = '1950s'
    DECADE_1940S = '1940s'
    DECADE_1930S = '1930s'
    DECADE_1920S = '1920s'
    DECADE_1910S = '1910s'
    DECADE_1900S = '1900s'
    DECADE_1890S = '1890s'
    DECADE_1880S = '1880s'
    DECADE_1870S = '1870s'
    UPCOMING = 'upcoming'

    @staticmethod
    def filter(url, decade):
        url += f'decade/{decade.value}/'
        return url


class TimePeriodSort(Enum):
    WEEK = 'week'
    MONTH = 'month'
    YEAR = 'year'

    @staticmethod
    def sort(url, timeframe):
        url += f'this/{timeframe.value}/'
        return url


class RatingRangeFilter(Enum):
    HALF_A_STAR = '.5'
    ONE_STAR = '1'
    ONE_AND_HALF_STAR = '1.5'
    TWO_STARS = '2'
    TWO_AND_HALF_STARS = '2.5'
    THREE_STARS = '3'
    THREE_AND_HALF_STARS = '3.5'
    FOUR_STARS = '4'
    FOUR_AND_HALF_STARS = '4.5'
    FIVE_STARS = '5'

    @staticmethod
    def filter(url, ratings):
        ratings = sorted(ratings, key=lambda r: float(r.value))
        url += f'rated/{ratings[0].value}-{ratings[1].value}/'
        return url


class SingleRatingFilter(Enum):
    HALF_A_STAR = '.5'
    ONE_STAR = '1.0'
    ONE_AND_HALF_STAR = '1.5'
    TWO_STARS = '2.0'
    TWO_AND_HALF_STARS = '2.5'
    THREE_STARS = '3.0'
    THREE_AND_HALF_STARS = '3.5'
    FOUR_STARS = '4.0'
    FOUR_AND_HALF_STARS = '4.5'
    FIVE_STARS = '5.0'
    NO_STARS = 'none'

    @staticmethod
    def filter(url, rating):
        url += f'rated/{rating.value}/'
        return url
