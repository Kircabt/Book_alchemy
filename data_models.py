from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Integer, ForeignKey

db = SQLAlchemy()

class Author(db.Model):
    __tablename__ = 'authors'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    birth_date = Column(String)
    date_of_death = Column(String)

    # Establishes a virtual relationship link to the Book model
    books = db.relationship('Book', back_populates='author', cascade="all, delete-orphan")

    def __repr__(self):
        return f"Author(id = {self.id}, name = {self.name})"

class Book(db.Model):
    __tablename__ = 'books'

    author_id = Column(Integer, ForeignKey('authors.id'), nullable=False)
    id = Column(Integer, primary_key=True, autoincrement=True)
    isbn = Column(String)
    title = Column(String)
    publication_year = Column(String)

    # Back-reference connection to the Author object
    author = db.relationship('Author', back_populates='books')

    def __repr__(self):
        return f"Book (id = {self.id}, name = {self.title})"

