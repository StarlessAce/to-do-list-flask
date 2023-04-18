from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base

# from flask_bootstrap import Bootstrap
# from flask_ckeditor import CKEditor
# from datetime import date
# from werkzeug.security import generate_password_hash, check_password_hash
# from sqlalchemy.orm import relationship
# from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
# from flask_gravatar import Gravatar
# from functools import wraps
# from flask import abort
#

## INITIALIZATION OF AN APP
app = Flask(__name__)
app.config['SECRET_KEY'] = 'githubversion'

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks1.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

Base = declarative_base()

done_list = []

class Task(db.Model, Base):
    __tablename__ = 'Tasks'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    priority = db.Column(db.Integer, nullable=False)
    deadline = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def get_all_tasks():
    if request.method == 'POST':
        task = Task(
            text=request.form['task'],
            description='add task descpription',
            priority=0,
            deadline='not assigned',
            status='not started'
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


@app.route("/done/<int:task_id>")
def move_to_done(task_id):

    done_list.append(Task.query.get(task_id))
    delete_task(task_id)
    return redirect(url_for('get_all_tasks'))



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)