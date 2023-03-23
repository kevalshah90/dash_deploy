from flask import Flask, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required
import sys
sys.path.append("..") # Adds higher directory to python modules path.
import os
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from index import application as dashApp

server_auth = Flask(__name__, instance_relative_config=False)

database = 'stroom_login'

server_auth.config['SECRET_KEY'] = 'GXvCqWhRoOuihe5'
server_auth.config['SQLALCHEMY_DATABASE_URI'] = "mysql://{}:{}@{}/{}".format(os.environ["user"], os.environ["pwd"], os.environ["host"], database)

# Update this for Production
server_auth.config['TESTING'] = True

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy(server_auth)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(server_auth)

from .models import users, init_db

with server_auth.app_context():
    init_db()

@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return users.query.get(int(user_id))

# blueprint for auth routes in our app
from .auth import auth as auth_blueprint
server_auth.register_blueprint(auth_blueprint)

# blueprint for non-auth parts of app
from .main import main as main_blueprint
server_auth.register_blueprint(main_blueprint)

# from .app import appdash as dash_blueprint
# app.register_blueprint(dash_blueprint)
# return server_auth

@server_auth.route('/dashboard')
@login_required
def dashboard():
    return redirect('/dashboard')

app = DispatcherMiddleware(server_auth,
                           {'/dashboard': dashApp.server})

# Change to port 80 to match the instance for AWS EB Environment
if __name__ == '__main__':
    run_simple('0.0.0.0', os.environ.get('DEBUG_PORT', 80), app, use_reloader=True, use_debugger=True)
