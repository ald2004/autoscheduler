from flask import Flask, request
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
api = Api(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///autosche.sqlite"
db = SQLAlchemy(app)

todos = {}

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    cfg = db.Column(db.String, unique=True, nullable=False)
#create table user(id smallint,username varchar(10),cfg text);

class TodoSimple(Resource):
    def get(self, todo_id):
        return {todo_id: todos[todo_id]}

    def put(self, todo_id):
        todos[todo_id] = request.form['data']
        db.session.add(User(username=str(todo_id), cfg=todos[todo_id]))
        db.session.commit()

        #users = User.query.all()
        return {todo_id: todos[todo_id]}

    def print(self,todo_id):
        return {todo_id,request.form['data']}

api.add_resource(TodoSimple, '/<string:todo_id>')

if __name__ == '__main__':
    app.run(debug=True)
