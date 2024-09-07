from api import create_app
from api.dataCollectors import FilmListCollector

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)