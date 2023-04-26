import datetime

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField

from flask_bootstrap import Bootstrap
# from flask_ckeditor import CKEditor
# from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
# from flask_gravatar import Gravatar
from functools import wraps
from flask import abort
#

## INITIALIZATION OF AN APP
app = Flask(__name__)
app.config['SECRET_KEY'] = 'githubversion'

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks1.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)
Base = declarative_base()

login_manager = LoginManager()
login_manager.init_app(app)


done_list = []


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    name = db.Column(db.String(250), nullable=False)


class Task(db.Model, Base):
    __tablename__ = 'Tasks'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    priority = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    deadline = db.Column(db.Integer, nullable=False)
    finished = db.Column(db.Boolean, nullable=False)
    start_date = db.Column(db.String(50), nullable=False)
    finish_date = db.Column(db.String(50), nullable=False)
    ontime = db.Column(db.Boolean, nullable=False)
    percentage = db.Column(db.Integer, nullable=False)


class Subtask(db.Model, Base):
    __tablename__ = 'Subtasks'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('Tasks.id'))
    text = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    finished = db.Column(db.Boolean, nullable=False)
    main_task = relationship('Task', backref='subtask')


class RegisterForm(FlaskForm):
    email = StringField("Your email", validators=[DataRequired()])
    password = PasswordField("password", validators=[DataRequired()])
    name = StringField("Type your name", validators=[DataRequired()])
    submit = SubmitField("Create")


class LoginForm(FlaskForm):
    email = StringField("Your email", validators=[DataRequired()])
    password = PasswordField("password", validators=[DataRequired()])
    submit = SubmitField("Let me in")


with app.app_context():
    db.create_all()


def check_approval(task_id):
    orig_task = Task.query.get(task_id)
    if not (Subtask.query.filter_by(task_id=task_id, status='In progress').all() or Subtask.query.filter_by(
            task_id=task_id, status='Not started').all()):
        if Subtask.query.filter_by(task_id=task_id, status='Finished').all():
            orig_task.status = 'Waiting for approval'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        user = User(
            email=form.email.data,
            password=hashed_password,
            name=form.name.data
        )
        db.session.add(user)
        db.session.commit()
        return render_template("index.html")
    return render_template("register.html", form=form, current_user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        password = request.form.get('password')
        if not user:
            error = 'No such user in the database'
            return render_template("login.html",form=form, error=error)
        elif check_password_hash(user.password, password):
            login_user(user)
            flash('You are successfully logged in!')
            return redirect("/")
        else:
            error = "Incorrect password"
    return render_template("login.html", form=form, error=error, current_user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_tasks'))


@app.route('/', methods=['GET', 'POST'])
def get_all_tasks():
    if request.method == 'POST':
        task = Task(
            text=request.form['task'],
            description='add task descpription',
            priority=0,
            deadline='not assigned',
            status='Not started'
        )
        db.session.add(task)
        db.session.commit()
    tasks = Task.query.all()
    return render_template("index.html", tasks=tasks, done=done_list)


@app.route("/delete/<int:task_id>")
def delete_task(task_id):
    task_to_delete = Task.query.get(task_id)
    db.session.delete(task_to_delete)
    db.session.commit()
    tasks = Task.query.all()
    return redirect(url_for('get_all_tasks'))


@app.route("/delete/<int:subtask_id>&<int:task_id>")
def delete_subtask(subtask_id, task_id):
    subtask_to_delete = Subtask.query.get(subtask_id)
    db.session.delete(subtask_to_delete)

    check_approval(task_id)

    db.session.commit()
    return redirect(url_for('show_task', task_id=task_id))


@app.route("/mark_as_progress/<int:subtask_id>&<int:task_id>")
def mark_as_progress(subtask_id, task_id):
    subtask = Subtask.query.get(subtask_id)
    orig_task = Task.query.get(task_id)
    if subtask.status != 'Not started':
        subtask.status = 'Not started'
    else:
        subtask.status = 'In progress'
    if Subtask.query.filter_by(task_id=task_id, status='In progress').all() or (Subtask.query.filter_by(task_id=task_id, status='Finished').all() and Subtask.query.filter_by(task_id=task_id, status='Not started')):
        orig_task.status = 'In progress'
    else:
        orig_task.status = 'Not started'

    db.session.commit()
    return redirect(url_for('show_task', task_id=task_id))


@app.route("/done/<int:task_id>")
def move_to_done(task_id):
    task = Task.query.get(task_id)
    now = datetime.datetime.now()
    finish_date = now.strftime("%m/%d/%Y")

    task.finish_date = finish_date
    task.status = 'Finished'
    task.finished = True
    task.ontime = True

    db.session.commit()
    done_list.append(Task.query.get(task_id))

    return redirect(url_for('get_all_tasks'))

@app.route("/done/<int:subtask_id>&<int:task_id>")
def move_subtask_to_done(subtask_id, task_id):
    subtask = Subtask.query.get(subtask_id)

    now = datetime.datetime.now()
    finish_date = now.strftime("%m/%d/%Y")

    subtask.finish_date = finish_date
    subtask.status = 'Finished'
    subtask.finished = True

    check_approval(task_id)

    db.session.commit()

    return redirect(url_for('show_task', task_id=task_id))


@app.route("/new-task", methods=['GET', 'POST'])
def new_task():
    if request.method == 'POST':
        now = datetime.datetime.now()
        start_date = now.strftime("%m/%d/%Y")
        try:
            description = request.form['description']
        except:
            description = ''
        task = Task(
            text=request.form['title'],
            description=description,
            priority=request.form['priority'],
            status='Not started',
            deadline=request.form['deadline'],
            finished=False,
            start_date=start_date,
            finish_date='',
            ontime=False,
            percentage=0
        )
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('get_all_tasks'))
    return render_template("new-task.html")


@app.route("/edit-task/<int:task_id>", methods=['GET', 'POST'])
def edit_task(task_id):
    task = Task.query.get(task_id)
    if request.method == 'POST':
        try:
            description = request.form['description']
        except:
            description = ''

        task.text = request.form['title']
        task.description = request.form['description']
        task.priority = request.form['priority']

        db.session.commit()

        return redirect(url_for('get_all_tasks'))
    return render_template("edit-task.html", task=task)



@app.route('/task/<int:task_id>', methods=['GET', 'POST'])
def show_task(task_id):
    task = Task.query.get(task_id)
    if request.method == 'POST':
        subtask = Subtask(
            text=request.form['task'],
            status='Not startedl',
            finished=False,
            main_task=task
        )
        db.session.add(subtask)
        db.session.commit()

        mark_as_progress(subtask_id=subtask.id, task_id=task_id)

    subtasks = Subtask.query.filter_by(task_id=task_id, finished=False).all()
    finished_subtasks = Subtask.query.filter_by(task_id=task_id, finished=True).all()
    all_subtasks = Subtask.query.filter_by(task_id=task_id).all()
    len_all = len(all_subtasks)
    len_finished = len(finished_subtasks)
    try:
        bar_percentage = int(len_finished / len_all * 100)
    except ZeroDivisionError:
        bar_percentage = 0

    task.percentage = bar_percentage
    db.session.commit()

    return render_template('task.html', task=task, subtasks=subtasks, finished_subtasks=finished_subtasks)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)