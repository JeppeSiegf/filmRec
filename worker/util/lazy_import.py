

def FilmListCollector(user, title, stopping_point):
    from dataCollectors.film_list_collector import FilmListCollector
    return FilmListCollector(user, title, stopping_point)


def FilmDetailCollector():
    from dataCollectors.film_detail_collector import FilmDetailCollector
    return FilmDetailCollector

def PageCollector():
    from dataCollectors.utils.page_collector import PageCollector
    return PageCollector

def RatingsCollector(user, stop_ref):
    from dataCollectors.ratings_collector import RatingsCollector
    return RatingsCollector(user, stop_ref,)

def UserListCollector(user):
    from dataCollectors.user_list_collector import UserListCollector
    return UserListCollector(user)

def MemberListCollector(film, stop_page, stop_user):
    from dataCollectors.member_collector import MemberListCollector
    return MemberListCollector(film, stop_page, stop_user)
