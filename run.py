
from api import create_app
from api.dataCollectors import film_list_collector

app = create_app()


if __name__ == "__main__":
    app.run()
