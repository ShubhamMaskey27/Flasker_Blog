from flask import Flask, render_template, flash, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from webforms import LoginForm, PostForm, UserForm, PasswordForm, NameForm, SearchForm
from flask_ckeditor import CKEditor
from werkzeug.utils import secure_filename
import uuid as uuid
import os


# Creating a flask instance
app = Flask(__name__)
# add CK editor instance
ckeditor = CKEditor(app)
# Secret key
app.config['SECRET_KEY'] = "my secret key "
# Old sqlite DB -Add database
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
# New Mysql Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:CProot@localhost/new_users'
# Initialise Database
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.app_context().push()
UPLOAD_FOLDER = 'static/images/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Flask Login Stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


# pass stuff to navbar to search
@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)


# Create a Admin Page
@app.route('/admin')
@login_required
def admin():
    # first_name = "john"
    id = current_user.id
    if id == 20:
        return render_template("admin.html")
    else:
        flash("Sorry you must be admin to access this Admin pages")
        return redirect(url_for('dashboard'))
    # first_name=first_name


# Create Search function
@app.route('/search', methods=['POST'])
def search():
    posts = Posts.query
    form = SearchForm()
    if form.validate_on_submit():
        # Get data from submitted form
        post.searched = form.searched.data
        # Query the database
        posts = posts.filter(Posts.content.like('%' + post.searched + '%'))
        posts = posts.order_by(Posts.title).all()
        return render_template('search.html',
                               form=form, searched=post.searched, posts=posts)


# Create Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # looked upto username we have submitted and grab  first one because unique
        user = Users.query.filter_by(username = form.username.data).first()
        if user:
            # Check the hash
            # this function return true if they match unless false
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("Login Successfull")
                return redirect(url_for('dashboard'))
            else:
                flash("Wrong password- Try again")
        else:
            flash("That user doesn't exist Try again")
    return render_template('login.html', form=form)


# Create logout Page
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("You Have Been Logged Out , Thanks for Stopping by..")
    return redirect(url_for('login'))


# Create Dashboard page
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    id = current_user.id
    form = UserForm()
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        # Passing information filled in the form to these variable
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.favorite_color = request.form['favorite_color']
        name_to_update.username = request.form['username']
        name_to_update.about_author = request.form['about_author']


        # check for profile pic
        if request.files['profile_pic']:
            name_to_update.profile_pic = request.files['profile_pic']
            # changing actual images to some random string
            # Grab image name
            pic_filename = secure_filename(name_to_update.profile_pic.filename)
            # Set UUID
            pic_name = str(uuid.uuid1()) + "_" + pic_filename
            # Save that image
            saver = request.files['profile_pic']
            # Change it to a string to save to db
            name_to_update.profile_pic = pic_name
            try:
                db.session.commit()
                saver.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
                flash("User updated successfully")
                return render_template("dashboard.html",
                                       form=form, name_to_update=name_to_update)
            except:
                flash("Looks like you messed Up")
                return render_template("dashboard.html",
                                       form=form, name_to_update=name_to_update)
        else:
            db.session.commit()
            flash("User updated successfully ")
            return render_template("dashboard.html",
                                   form=form, name_to_update=name_to_update)
    else:
        return render_template("dashboard.html", form=form, name_to_update=name_to_update)


@app.route('/post/delete/<int:id>')
@login_required
def delete_post(id):
    post_to_delete = Posts.query.get_or_404(id)
    # Allow only authorised user to delete his post
    id = current_user.id
    if id == post_to_delete.poster.id or id == 24:
        try:
            db.session.delete(post_to_delete)
            db.session.commit()
            flash("Blog Post Deleted")
            # Grab all the posts from the database
            posts = Posts.query.order_by(Posts.date_posted)
            return render_template("posts.html", posts=posts)
        except:
            flash("Whoopsie, There was a problem deleting post.. try again ")
            # Grab all the posts from the database
            posts = Posts.query.order_by(Posts.date_posted)
            return render_template("posts.html", posts=posts)
    else:
        # if someone who is not authorised
        flash("You are not authorised to Delete that post")
        # Grab all the posts from the database
        posts = Posts.query.order_by(Posts.date_posted)
        return render_template("posts.html", posts=posts)


@app.route('/posts')
def posts():
    # This grab all the post from database
    posts = Posts.query.order_by(Posts.date_posted)
    return render_template("posts.html", posts=posts)


@app.route('/posts/<int:id>')
def post(id):
    post = Posts.query.get_or_404(id)
    return render_template('post.html', post=post)


@app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Posts.query.get_or_404(id)
    form = PostForm()
    # actually someone submitting any change
    # after clicking edit button these things called up
    if form.validate_on_submit():
        post.title = form.title.data
        # post.author = form.author.data
        post.slug = form.slug.data
        post.content = form.content.data
        # Update database
        db.session.add(post)
        db.session.commit()
        flash("Post Has Been Updated")
        return redirect(url_for('post', id=post.id))
    # this stuff passing information for the first time so that we don't have to retype'
    if current_user.id == post.poster_id:
        form.title.data = post.title
        # form.author.data = post.author
        form.slug.data = post.slug
        form.content.data = post.content
        return render_template('edit_post.html', form=form)
    else:
        flash("You aren't authorised to edit this page")
        posts = Posts.query.order_by(Posts.date_posted)
        return render_template("posts.html", posts=posts)


# Add post page
@app.route('/add-post', methods=['GET', 'POST'])
@login_required
def add_post():
    form = PostForm()
    if form.validate_on_submit():
        poster = current_user.id
        # Our model name POSTS
        post = Posts(title=form.title.data, content=form.content.data, poster_id = poster, slug=form.slug.data)
        # after submitting we have to clear the form
        form.title.data = ''
        form.content.data = ''
        form.slug.data = ''

        # add post data to database
        db.session.add(post)
        db.session.commit()

        flash("Blog Post submitted Successfully")
    # Redirect to the webpage
    return render_template("add_post.html", form=form)


# Json Thing
@app.route('/date')
def get_current_date():
    favorite_pizza = {
        "Lambo": "Roadster",
        "Porsche": "911",
        "Audi": "A6"
    }
    # return favorite_pizza
    return {"Date": date.today()}

    @property
    def password(self):
        raise AttributeError('Password is not a readable point')

    @password.setter
    def password(self, password):
        # Take whatever they put in password field and generate a hashed password
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Create a String
    def __repr__(self):
        return '<Name %r>' % self.name


@app.route('/delete/<int:id>')
@login_required
def delete(id):
    user_to_delete = Users.query.get_or_404(id)
    name = None
    form = UserForm()

    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash("user deleted successfully")

        our_users = Users.query.order_by(Users.date_added)
        return render_template("add_user.html", form=form,
                               name=name,
                               our_users=our_users)
    except:
        flash("There was a problem deleting a user")
        return render_template("add_user.html", form=form,
                               name=name,
                               our_users=our_users)


# Update database record
@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    if id == current_user.id:
        form = UserForm()
        name_to_update = Users.query.get_or_404(id)
        if request.method == "POST":
            # Passing information filled in the form to these variable
            name_to_update.name = request.form['name']
            name_to_update.email = request.form['email']
            name_to_update.favorite_color = request.form['favorite_color']
            name_to_update.username = request.form['username']
            try:
                db.session.commit()
                flash("User updated successfully")
                return render_template("update.html",
                                       form=form, name_to_update=name_to_update, id=id)
            except:
                flash("Looks like you messed Up")
                return render_template("update.html",
                                       form=form, name_to_update=name_to_update, id=id)
        return render_template("update.html", form=form, name_to_update=name_to_update, id=id)
    else:
        flash("Sorry you can't delete ,Looks like you messed Up")
        return redirect(url_for('dashboard'))


@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            # Hash the Password
            hashed_pw = generate_password_hash(form.password_hash.data, "sha256")
            user = Users(username=form.username.data, name=form.name.data, email=form.email.data, favorite_color=form.favorite_color.data,
                         password_hash=hashed_pw)
            db.session.add(user)
            db.session.commit()

        name = form.name.data
        form.username.data = ''
        form.name.data = ''
        form.email.data = ''
        form.favorite_color.data = ''
        form.password_hash = ''
        flash("User Added Successfully")
    our_users = Users.query.order_by(Users.date_added)
    return render_template("add_user.html", form=form,
                           name=name,
                           our_users=our_users)


# Create a route decorator
@app.route('/')
def index():
    # first_name = "john"
    flash("Welcome to our Website")
    return render_template('index.html')  # first_name=first_name


@app.route('/user/<name>')
def user(name):
    return render_template('user.html', user_name=name)


# Custom error pages
# Invalid URl
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500


# Create a password page
@app.route('/test_pw', methods=['GET', 'POST'])
def test_pw():
    email = None
    password = None
    pw_to_check = None
    passed = None

    # Here we are passing Password form here
    form = PasswordForm()
    # Validate Form
    if form.validate_on_submit():
        email = form.email.data
        password = form.password_hash.data
        form.email.data = ''
        form.password_hash.data = ''
        # look up user by email address
        pw_to_check = Users.query.filter_by(email=email).first()
        # Check hashed Password
        passed = check_password_hash(pw_to_check.password_hash, password)
    return render_template("test_pw.html",
                           pw_to_check=pw_to_check,
                           password=password,
                           name=name,
                           passed=passed,
                           form=form)


# Create a name page
@app.route('/name', methods=['GET', 'POST'])
def name():
    name = None
    form = NameForm()
    # Validate Form
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
        flash("Form Submitted Successfully")
    return render_template("name.html",
                           name=name,
                           form=form)


# Database


# Create a Blog Post model
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    # author = db.Column(db.String(255))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    slug = db.Column(db.String(255))
    # Foreign Key to link Users (refer to primary key of the user)
    poster_id = db.Column(db.Integer, db.ForeignKey("users.id"))


# Create Model
class Users(db.Model, UserMixin):
    username = db.Column(db.String(20), nullable=False, unique=True)
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    favorite_color = db.Column(db.String(120))
    about_author = db.Column(db.Text(500), nullable=True)
    profile_pic = db.Column(db.String(100), nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    # do some password stuff
    password_hash = db.Column(db.String(128))
    # Users can have many posts, Capital Posts reference to class not column
    posts = db.relationship('Posts', backref='poster')


if __name__ == "__main__":
    app.run(debug=True)

