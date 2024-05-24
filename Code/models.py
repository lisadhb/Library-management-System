from app import app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

db=SQLAlchemy(app)

class User(db.Model):
    user_id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(32),unique=True)
    passhash=db.Column(db.String(256),nullable=False)
    name=db.Column(db.String(64),nullable=True)
    is_admin=db.Column(db.Boolean,nullable=False,default=False)
    current_requests = db.Column(db.Integer, nullable=False, default=0)

    requests = db.relationship('BookRequest', backref='user', lazy=True, cascade="all, delete-orphan")
    accesses = db.relationship('BookAccess', backref='user', lazy=True, cascade="all, delete-orphan")

class Section(db.Model):
    sec_id=db.Column(db.Integer,primary_key=True)
    sec_name=db.Column(db.String(64),unique=True)
    datetime=db.Column(db.DateTime,nullable=False)
    description=db.Column(db.String(256),nullable=False)
    
    books=db.relationship('Books',backref='section',lazy=True,cascade="all, delete-orphan")

class Books(db.Model):
    book_id=db.Column(db.Integer,primary_key=True)
    b_name=db.Column(db.String(64),nullable=False)
    sec_id=db.Column(db.Integer,db.ForeignKey('section.sec_id'),nullable=False)
    b_content=db.Column(db.String(256),nullable=False)
    auth_name=db.Column(db.String(64),nullable=False)
    current_requests = db.Column(db.Integer, nullable=False, default=0)

    requests = db.relationship('BookRequest', backref='books', lazy=True, cascade="all, delete-orphan")
    accesses = db.relationship('BookAccess', backref='books', lazy=True, cascade="all, delete-orphan")

class BookRequest(db.Model):
    request_id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('user.user_id'),nullable=False)
    book_id=db.Column(db.Integer,db.ForeignKey('books.book_id'),nullable=False)
    request_date=db.Column(db.DateTime,nullable=False)
    return_date=db.Column(db.DateTime,nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')

class BookAccess(db.Model):
    access_id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('user.user_id'),nullable=False)
    book_id=db.Column(db.Integer,db.ForeignKey('books.book_id'),nullable=False)
    access_date=db.Column(db.DateTime,nullable=False)
    expiration_date=db.Column(db.DateTime,nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')

with app.app_context():
    db.create_all()

    admin = User.query.filter_by(is_admin=True).first()
    if admin is None:
        password_hash=generate_password_hash('admin')
        admin=User(username='admin',passhash=password_hash,name='Admin',is_admin=True)
        db.session.add(admin)
        db.session.commit()