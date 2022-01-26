from flask import Flask
import os

server_auth = Flask(__name__,instance_relative_config=False)

server_auth.config['SECRET_KEY'] = 'GXvCqWhRoORbMfFdiQGs'
server_auth.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
server_auth.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
