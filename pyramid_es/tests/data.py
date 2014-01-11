from hashlib import sha1

from sqlalchemy import Column, ForeignKey, types, orm
from sqlalchemy.ext.declarative import declarative_base

from ..mixin import ElasticMixin, ESMapping, ESString, ESField


Base = declarative_base()


class Genre(Base, ElasticMixin):
    __tablename__ = 'genres'
    id = Column(types.String(40), primary_key=True)
    title = Column(types.Unicode(40))

    def __init__(self, *args, **kwargs):
        Base.__init__(self, *args, **kwargs)
        self.id = sha1(self.title.encode('utf-8')).hexdigest()

    @classmethod
    def elastic_mapping(cls):
        return ESMapping(
            analyzer='content',
            properties=ESMapping(
                ESString('title', boost=5.0)))


class Movie(Base, ElasticMixin):
    __tablename__ = 'movies'
    id = Column(types.String(40), primary_key=True)
    title = Column(types.Unicode(40))
    director = Column(types.Unicode(40))
    year = Column(types.Integer)
    rating = Column(types.Numeric)
    genre_id = Column(None, ForeignKey('genres.id'))

    genre = orm.relationship('Genre')

    __elastic_parent__ = ('Genre', 'genre_id')

    def __init__(self, *args, **kwargs):
        Base.__init__(self, *args, **kwargs)
        self.id = sha1(self.title.encode('utf-8')).hexdigest()

    @property
    def genre_title(self):
        return self.genre.title

    @classmethod
    def elastic_mapping(cls):
        return ESMapping(
            analyzer='content',
            properties=ESMapping(
                ESString('title', boost=5.0),
                ESString('director'),
                ESField('year'),
                ESField('rating'),
                ESString('genre_title', analyzer='lowercase')))


class Unindexed(Base):
    # Does not inherit from ElasticMixin.
    __tablename__ = 'unindexed'
    id = Column(types.Integer, primary_key=True)


def get_data():
    mystery = Genre(title=u'Mystery')
    comedy = Genre(title=u'Comedy')
    action = Genre(title=u'Action')
    drama = Genre(title=u'Drama')

    genres = [mystery, comedy, action, drama]

    movies = [
        Movie(
            title=u'To Catch a Thief',
            director=u'Alfred Hitchcock',
            year=1955,
            rating=7.5,
            genre=mystery,
            genre_id=mystery.id,
        ),
        Movie(
            title=u'Vertigo',
            director=u'Alfred Hitchcock',
            year=1958,
            rating=8.5,
            genre=mystery,
            genre_id=mystery.id,
        ),
        Movie(
            title=u'North by Northwest',
            director=u'Alfred Hitchcock',
            year=1959,
            rating=8.5,
            genre=mystery,
            genre_id=mystery.id,
        ),
        Movie(
            title=u'Destination Tokyo',
            director=u'Delmer Daves',
            year=1943,
            rating=7.1,
            genre=action,
            genre_id=action.id,
        ),
        Movie(
            title=u'Annie Hall',
            director=u'Woody Allen',
            year=1977,
            rating=8.2,
            genre=comedy,
            genre_id=comedy.id,
        ),
        Movie(
            title=u'Sleeper',
            director=u'Woody Allen',
            year=1973,
            rating=7.3,
            genre=comedy,
            genre_id=comedy.id,
        ),
        Movie(
            title=u'Captain Blood',
            director=u'Michael Curtiz',
            year=1935,
            rating=7.8,
            genre=action,
            genre_id=action.id,
        ),
        Movie(
            title=u'Metropolis',
            director=u'Fritz Lang',
            year=1927,
            rating=8.4,
            genre=drama,
            genre_id=drama.id,
        )]
    return genres, movies
