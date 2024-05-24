from datetime import datetime, timedelta
from functools import wraps
from app import app
from flask import flash, redirect, render_template, request, session, url_for
from models import *
from werkzeug.security import generate_password_hash,check_password_hash 


# general routes
@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login',methods=['POST'])
def login_post():
    username=request.form.get('uname')
    password=request.form.get('pass')

    if not username or not password:
        flash("Please fill all the details!")
        return redirect(url_for('login'))
    
    user=User.query.filter_by(username=username).first()
    if not user:
        flash("Username does not exists!")
        return redirect(url_for('login'))
    
    if not check_password_hash(user.passhash, password):
        flash("Incorrect password")
        return redirect(url_for('login'))
    
    session['user_id']=user.user_id
    flash("Login successful!")
    return redirect(url_for('index'))

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register',methods=['POST'])
def register_post():
    username=request.form.get('uname')
    name=request.form.get('name')
    password=request.form.get('pass')
    confirm_password=request.form.get('cpass')

    if not username or not password or not confirm_password:
        flash("Please fill all the details!")
        return redirect(url_for('register'))
    
    if password!=confirm_password:
        flash("Password does not match!")
        return redirect(url_for('register'))
    
    user=User.query.filter_by(username=username).first()
    if user:
        flash("Username already exists!")
        return redirect(url_for('register'))
    
    password_hash=generate_password_hash(password)
    new_user=User(username=username,passhash=password_hash,name=name)
    db.session.add(new_user)
    db.session.commit()
    flash("Registered successfully!")
    return redirect(url_for('login'))

# authentication
def auth_required(func):
    @wraps(func)
    def inner(*args,**kwargs):
        if 'user_id' in session:
            return func(*args,**kwargs)
        else:
            flash('Please login to continue!')
            return redirect(url_for('login'))
    return inner

def admin_required(func):
    @wraps(func)
    def inner(*args,**kwargs):
        if 'user_id' not in session:
            flash('Please login to continue!')
            return redirect(url_for('login'))
        user=User.query.get(session['user_id'])
        if not user.is_admin:
            flash('Not authorized')
            return redirect(url_for('index'))
        return func(*args,**kwargs)
    return inner

# user routes
@app.route('/')
@auth_required
def index():
    user=User.query.get(session['user_id'])
    if user.is_admin:
        return redirect(url_for('admin'))
    sections=Section.query.all()
    sname=request.args.get('sname') or ''
    bname=request.args.get('bname') or ''
    auth_name=request.args.get('auth_name') or ''
    if sname:
        sections=Section.query.filter(Section.sec_name.ilike(f'%{sname}%')).all()
    return render_template('index.html',sections=sections,sname=sname,bname=bname,auth_name=auth_name)

@app.route('/user-profile')
@auth_required
def user_profile():
    user = User.query.get(session['user_id'])
    num_requests = len(user.requests)
    num_books = len(user.accesses)
    is_admin = User.query.filter_by(user_id=session.get('user_id'), is_admin=True).first() is not None
    return render_template('user_profile.html', user=user, num_requests=num_requests, num_books=num_books, is_admin=is_admin)

@app.route('/admin-profile')
@admin_required
def admin_profile():
    user = User.query.get(session['user_id'])
    num_sections = len(Section.query.all())
    num_books = len(Books.query.all())
    requested_books = len(BookRequest.query.filter_by(status='pending').all())
    issued_books = len(BookAccess.query.filter_by(status='accepted').all())
    sections=Section.query.all()
    section_names=[section.sec_name for section in sections]
    section_sizes=[len(section.books) for section in sections]
    is_admin = User.query.filter_by(user_id=session.get('user_id'), is_admin=True).first() is not None
    return render_template('admin_profile.html', user=user,num_sections=num_sections, num_books=num_books, requested_books=requested_books, issued_books=issued_books, is_admin=is_admin,section_names=section_names,section_sizes=section_sizes)

@app.route('/request/<int:book_id>')
@auth_required
def request_book(book_id):
    book=Books.query.get(book_id)
    if not book:
        flash("Book does not exist!")
        return redirect(url_for('index'))
    user_id = session.get('user_id')
    user_requests_count = BookRequest.query.filter_by(user_id=user_id).count()
    if user_requests_count >= 5:
        flash("You have already reached the maximum number of requests.")
        return redirect(url_for('index'))
    existing_request = BookRequest.query.filter_by(user_id=user_id, book_id=book_id).first()
    if existing_request:
        flash(f"You have already requested {book.b_name}!")
        return redirect(url_for('index'))
    return render_template('request.html', book=book)

@app.route('/request/<int:book_id>',methods=['POST'])
@auth_required
def request_book_post(book_id):
    book = Books.query.get(book_id)
    if not book:
        flash("Book does not exist!")
        return redirect(url_for('index'))
    user_id = session.get('user_id')
    user_requests_count = BookRequest.query.filter_by(user_id=user_id).count()
    if user_requests_count >= 5:
        flash("You have already reached the maximum number of requests.")
        return redirect(url_for('index'))
    existing_request = BookRequest.query.filter_by(user_id=user_id, book_id=book_id).first()
    if existing_request:
        flash(f"You have already requested {book.b_name}!")
        return redirect(url_for('index'))
    new_request = BookRequest(user_id=user_id, book_id=book_id, request_date=datetime.now(), return_date=datetime.now() + timedelta(days=7))
    db.session.add(new_request)
    db.session.commit()
    flash(f"{book.b_name} has been requested successfully!")
    return redirect(url_for('index'))

@app.route('/user-requests')
@auth_required
def user_requests():
    user_id = session.get('user_id')
    user_requests = BookRequest.query.filter_by(user_id=user_id).all()  
    return render_template('user_requests.html', requests=user_requests) 


@app.route('/cancel_request/<int:request_id>', methods=['POST'])
@auth_required
def cancel_request(request_id):
    user_id = session.get('user_id')
    request = BookRequest.query.filter_by(request_id=request_id, user_id=user_id).first()
    if not request:
        flash("Request not found!")
    else:
        db.session.delete(request)
        db.session.commit()
        flash("Request canceled successfully.")
    return redirect(url_for('user_requests'))

@app.route('/mybooks')
@auth_required
def my_books():
    user_id = session.get('user_id')
    user_books = BookAccess.query.filter_by(user_id=user_id, status='accepted').all()
    return render_template('my_books.html', books=user_books)

@app.route('/view_book/<int:book_id>')
@auth_required
def view_content(book_id):
    book = Books.query.get(book_id)
    if not book:
        flash("Book not found!")
        return redirect(url_for('my_books'))
    return render_template('book_content.html', book=book)

@app.route('/return_book/<int:book_id>')
@auth_required
def return_book(book_id):
    user_id = session.get('user_id')
    book_access = BookAccess.query.filter_by(user_id=user_id, book_id=book_id).first()
    if not book_access:
        flash("Book not found in your collection!")
        return redirect(url_for('my_books'))
    book = Books.query.get(book_id)
    return render_template('return.html',book=book)

@app.route('/return_book/<int:book_id>', methods=['POST'])
@auth_required
def return_book_post(book_id):
    user_id = session.get('user_id')
    book_access = BookAccess.query.filter_by(user_id=user_id, book_id=book_id).first()
    if not book_access:
        flash("Book not found in your collection!")
        return redirect(url_for('my_books'))
    db.session.delete(book_access)
    db.session.commit()
    flash("Book returned successfully!")
    return redirect(url_for('my_books'))

@app.route('/logout')
@auth_required
def logout():
    session.pop('user_id')
    flash("Logged out successfully!")
    return redirect(url_for('login'))

# admin routes
@app.route('/admin')
@admin_required
def admin():
    sections=Section.query.all()
    is_admin = User.query.filter_by(user_id=session.get('user_id'), is_admin=True).first() is not None
    return render_template('admin.html',sections=sections,is_admin=is_admin)

@app.route('/section/add')
@admin_required
def add_section():
    is_admin = User.query.filter_by(user_id=session.get('user_id'), is_admin=True).first() is not None
    return render_template('section/add.html',is_admin=is_admin)

@app.route('/section/add',methods=['POST'])
@admin_required
def add_section_post():
    name=request.form.get('name')
    des=request.form.get('des')
    if not name:
        flash("Please fill all details!")
        return redirect(url_for('add_section'))
    section=Section(sec_name=name,datetime=datetime.now().date(),description=des)
    db.session.add(section)
    db.session.commit()
    flash("Section added successfully!")
    return redirect(url_for('admin'))

@app.route('/section/<int:sec_id>/')
@admin_required
def view_section(sec_id):
    section=Section.query.get(sec_id)
    is_admin = User.query.filter_by(user_id=session.get('user_id'), is_admin=True).first() is not None
    if not section:
        flash('Category does not exist')
        return redirect(url_for('admin'))
    return render_template('section/view.html',section=section,is_admin=is_admin)

@app.route('/section/<int:sec_id>/edit')
@admin_required
def edit_section(sec_id):
    section=Section.query.get(sec_id)
    is_admin = User.query.filter_by(user_id=session.get('user_id'), is_admin=True).first() is not None
    if not section:
        flash("Section does not exist!")
        return redirect(url_for('admin'))
    return render_template('section/edit.html',is_admin=is_admin,section=section)

@app.route('/section/<int:sec_id>/edit',methods=['POST'])
@admin_required
def edit_section_post(sec_id):
    section=Section.query.get(sec_id)
    if not section:
        flash("Section does not exist!")
        return redirect(url_for('admin'))
    name=request.form.get('name')
    des = request.form.get('des')
    if not name or not des:
        flash("Please fill all details!")
        return redirect(url_for('edit_section',section=section))
    section.sec_name=name
    section.des = des
    db.session.commit()
    flash("Section updated successfully")
    return redirect(url_for('admin'))


@app.route('/section/<int:sec_id>/delete')
@admin_required
def delete_section(sec_id):
    section=Section.query.get(sec_id)
    is_admin = User.query.filter_by(user_id=session.get('user_id'), is_admin=True).first() is not None
    if not section:
        flash("Section does not exist!")
        return redirect(url_for('admin'))
    return render_template('section/delete.html',is_admin=is_admin,section=section)

@app.route('/section/<int:sec_id>/delete',methods=['POST'])
@admin_required
def delete_section_post(sec_id):
    section=Section.query.get(sec_id)
    if not section:
        flash("Section does not exist!")
        return redirect(url_for('admin'))
    db.session.delete(section)
    db.session.commit()
    flash("Section deleted successfully")
    return redirect(url_for('admin'))

@app.route('/book/add/<int:sec_id>')
@admin_required
def add_book(sec_id):
    sections=Section.query.all()
    section=Section.query.get(sec_id)
    is_admin = User.query.filter_by(user_id=session.get('user_id'), is_admin=True).first() is not None
    if not section:
        flash("Section does not exist!")
        return redirect(url_for('admin'))
    return render_template('book/add.html',is_admin=is_admin,section=section,sections=sections)

@app.route('/book/add/',methods=['POST'])
@admin_required
def add_book_post():
    name=request.form.get('name')
    content=request.form.get('content')
    author=request.form.get('author')
    sec_id=request.form.get('sec_id')

    section=Section.query.get(sec_id)
    if not section:
        flash("Section does not exist!")
        return redirect(url_for('admin'))
    if not name or not author  or not content:
        flash("Please fill all details!")
        return redirect(url_for('add_book',sec_id=sec_id))

    book=Books(b_name=name,section=section,auth_name=author,b_content=content)
    db.session.add(book)
    db.session.commit()
    flash("Book added successfully!")
    return redirect(url_for('admin'))

@app.route('/book/edit/<int:book_id>')
@admin_required
def edit_book(book_id):
    sections=Section.query.all()
    book=Books.query.get(book_id)
    is_admin = User.query.filter_by(user_id=session.get('user_id'), is_admin=True).first() is not None
    return render_template('book/edit.html',is_admin=is_admin,book=book,sections=sections)

@app.route('/book/edit/<int:book_id>',methods=['POST'])
@admin_required
def edit_book_post(book_id):
    name=request.form.get('name')
    des=request.form.get('des')
    author=request.form.get('author')
    sec_id=request.form.get('sec_id')

    section=Section.query.get(sec_id)
    if not section:
        flash("Section does not exist!")
        return redirect(url_for('admin'))
    if not name or not author or not des:
        flash("Please fill all details!")
        return redirect(url_for('edit_book',book_id=book_id))
    book=Books.query.get(book_id)
    book.b_name=name
    book.section=section
    book.auth_name=author
    book.b_content=des
    db.session.commit()
    flash("Book edited successfully!")
    return redirect(url_for('view_section',sec_id=sec_id))

@app.route('/book/view/<int:book_id>')
@admin_required
def view_book(book_id):
    book=Books.query.get(book_id)
    sec_id=book.section.sec_id
    is_admin = User.query.filter_by(user_id=session.get('user_id'), is_admin=True).first() is not None
    if not book:
        flash("Book does not exist!")
        return redirect(url_for('view_section',sec_id=sec_id))
    return render_template('book/view.html',is_admin=is_admin,book=book)

@app.route('/book/delete/<int:book_id>')
@admin_required
def delete_book(book_id):
    book=Books.query.get(book_id)
    sec_id=book.section.sec_id
    is_admin = User.query.filter_by(user_id=session.get('user_id'), is_admin=True).first() is not None
    if not book:
        flash("Book does not exist!")
        return redirect(url_for('view_section',sec_id=sec_id))
    return render_template('book/delete.html',is_admin=is_admin,book=book)

@app.route('/book/<int:book_id>/delete',methods=['POST'])
@admin_required
def delete_book_post(book_id):
    book=Books.query.get(book_id)
    if not book:
        flash("Book does not exist!")
        return redirect(url_for('admin'))
    sec_id=book.section.sec_id
    db.session.delete(book)
    db.session.commit()
    flash("Book deleted successfully")
    return redirect(url_for('view_section',sec_id=sec_id))

@app.route('/manage-requests')
@admin_required
def manage_requests():
    all_requests = BookRequest.query.all()
    is_admin = User.query.filter_by(user_id=session.get('user_id'), is_admin=True).first() is not None
    return render_template('manage_requests.html',is_admin=is_admin, requests=all_requests)

@app.route('/accept_request', methods=['POST'])
@admin_required
def accept_request():
    if request.method == 'POST':
        request_id = request.form.get('request_id')
        req = BookRequest.query.get(request_id)
        if not req:
            flash("Request not found!")
            return redirect(url_for('manage_requests'))
        new_access = BookAccess(user_id=req.user_id, book_id=req.book_id, access_date=datetime.now(), expiration_date=datetime.now() + timedelta(days=7), status='accepted')
        db.session.add(new_access)
        db.session.delete(req)
        db.session.commit()
        flash("Request accepted successfully!")
        return redirect(url_for('manage_requests'))

@app.route('/manage_issues')
@admin_required
def manage_issues():
    accepted_books = BookAccess.query.filter_by(status='accepted').all()
    is_admin = User.query.filter_by(user_id=session.get('user_id'), is_admin=True).first() is not None
    return render_template('manage_issues.html',is_admin=is_admin, accepted_books=accepted_books)

@app.route('/revoke_book/<int:book_id>', methods=['POST'])
@admin_required
def revoke_book(book_id):
    book_access = BookAccess.query.filter_by(book_id=book_id).first()
    if not book_access:
        flash("Book access not found!")
    else:
        db.session.delete(book_access)
        db.session.commit()
        flash("Book access revoked successfully!")
    return redirect(url_for('manage_issues'))

@app.route('/decline_request', methods=['POST'])
@admin_required
def decline_request():
    if request.method == 'POST':
        request_id = request.form.get('request_id')
        req = BookRequest.query.get(request_id)
        if not req:
            flash("Request not found!")
        else:
            db.session.delete(req)
            db.session.commit()
            flash("Request declined successfully!")
    return redirect(url_for('manage_requests'))
