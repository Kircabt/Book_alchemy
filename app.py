from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
import os
from data_models import db, Author, Book


app = Flask(__name__)
app.secret_key = 'change-me-in-production'  # flash() needs a secret key
basedir = os.path.abspath(os.path.dirname(__file__))
os.makedirs(os.path.join(basedir, 'data'), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"


db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    if request.method == 'POST':
        # Retrieve input data from the form fields
        author_name = request.form.get('name')
        birth_date = request.form.get('birthdate')
        date_of_death = request.form.get('date_of_death') or None

        # Instantiate the new record (omitting 'id' as it autoincrements)
        new_author = Author(name=author_name, birth_date=birth_date, date_of_death=date_of_death)

        # Save to the database using SQLAlchemy
        db.session.add(new_author)
        db.session.commit()

        # Send a success message back to the template
        flash(f"Author '{author_name}' was successfully added!", "success")

        # Redirect back to the same page to prevent double-submits on refresh
        return redirect(url_for('add_author'))

    # GET request: Renders the blank form template
    return render_template('add_author.html')


# --- NEW /ADD_BOOK ROUTE ---
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        # Retrieve input data from the form fields
        book_title = request.form.get('title')
        pub_year = request.form.get('publication_year')
        selected_author_id = request.form.get('author_id', type=int)
        book_isbn = request.form.get('isbn')

        # Validate the selected author
        author = db.session.get(Author, selected_author_id) if selected_author_id else None

        if not author:
            flash("Please select a valid author.", "error")
            return redirect(url_for('add_book'))

        # Instantiate the new Book record
        new_book = Book(
            title=book_title,
            isbn=book_isbn,
            publication_year=pub_year or None,  # Handles optional year safely
            author_id=author.id
        )

        # Save to the database
        db.session.add(new_book)
        db.session.commit()

        # Send a success message back to the template
        flash(f"Book '{book_title}' was successfully added!", "success")

        # Redirect to prevent double-submits on browser refresh
        return redirect(url_for('add_book'))

    # GET request: Query all authors so they can populate the dropdown selection
    all_authors = db.session.query(Author).order_by(Author.name).all()
    return render_template('add_book.html', authors=all_authors)


@app.route('/')
def home():
    # Read the sorting choice from the URL, e.g. /?sort=author&order=desc
    sort = request.args.get('sort', 'title')
    order = request.args.get('order', 'asc')

    # Whitelist of sortable columns (never trust raw user input in a query)
    sort_columns = {
        'title': Book.title,
        'author': Author.name,
        'year': Book.publication_year,
    }
    if sort not in sort_columns:
        sort = 'title'
    if order not in ('asc', 'desc'):
        order = 'asc'

    column = sort_columns[sort]
    column = column.desc() if order == 'desc' else column.asc()

    # Search text from the form, e.g. /?q=hobbit
    search = request.args.get('q', '').strip()

    # Join Author so books can be ordered by the author's name
    query = db.session.query(Book).join(Author, Book.author_id == Author.id)

    if search:
        # ilike = case-insensitive LIKE '%search%' (matches title or author name)
        pattern = f"%{search}%"
        query = query.filter(
            or_(Book.title.ilike(pattern), Author.name.ilike(pattern))
        )

    all_books = query.order_by(column, Book.title).all()

    # Return the template and pass the data in the format Jinja expects
    return render_template('home.html', books=all_books, sort=sort, order=order, search=search)

@app.route('/book/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    # 404 if there is no book with this id
    book = db.get_or_404(Book, book_id)
    title = book.title
    author = book.author

    db.session.delete(book)
    db.session.flush()  # apply the delete so the count below no longer includes this book

    message = f"Book '{title}' was successfully deleted!"

    # If the author has no other books left, remove the author as well
    remaining = db.session.query(Book).filter_by(author_id=author.id).count()
    if remaining == 0:
        db.session.delete(author)
        message = f"Book '{title}' and its author '{author.name}' were successfully deleted!"

    db.session.commit()
    flash(message, "success")
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
