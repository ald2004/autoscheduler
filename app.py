from flask import Flask, request
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
import docker
import json
import threading
from flask import flash
import time

app = Flask(__name__)
api = Api(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///autosche.sqlite"
db = SQLAlchemy(app)

todos = {}
cli = docker.from_env()


class Images(db.Model):
    # repository = db.Column(db.text)
    image_id = db.Column(db.Text, primary_key=True)
    created = db.Column(db.Text)
    size = db.Column(db.Text)
    labels = db.Column(db.Text)
    short_id = db.Column(db.Text)
    tags = db.Column(db.Text)
    lifes = db.Column(db.INT)
    counts = db.Column(db.INT)


class Instance(db.Model):
    id = db.Column(db.Text, primary_key=True)
    created = db.Column(db.Text)
    state = db.Column(db.Text)
    image_id = db.Column(db.Text)
    mounts = db.Column(db.Text)
    short_image_id = db.Column(db.Text)
    config = db.Column(db.Text)
    network_config = db.Column(db.Text)
    status = db.Column(db.Text)


class TodoSimple(Resource):
    def get(self):
        for image in cli.images.list():
            try:
                mtn = image.labels['maintainer']
            except:
                mtn = ''
            # try:

            db.session.merge(Images(
                image_id=image.id, created=image.attrs['Created'],
                size=f"{image.attrs['Size'] / (1000 ** 3)}GB",
                labels=mtn,
                short_id=image.short_id, tags=','.join(image.tags),
                lifes=0,counts=0
            ))
        db.session.commit()
        # except Exception as inst:
        #     print(type(inst))  # the exception instance
        #     print(inst.args)  # arguments stored in .args
        #     print(inst)
        #     return {'init':'fail'}

        return {'init': 'succ'}

    def put(self, todo_id):
        # todos[todo_id] = request.form['data']
        # db.session.add(User(username=str(todo_id), cfg=todos[todo_id]))
        # db.session.commit()

        # users = User.query.all()
        return {'iputnit': 'succ'}


def dae_maintain_insx(cli: docker.client.DockerClient):
    while 1:
        copies = {"image_id": 0}  # 'sha256:76c152fbf...'
        copies ={}
        ins = cli.containers.list(all=True)
        for i in ins:
            if i.status.startswith('running'):  # running exited created
                copies[i.image.id] = copies.get(i.image.id) + 1 if copies.get(i.image.id) else 1
            db.session.merge(Instance(
                id=i.id, created=i.attrs['Created'],
                state=json.dumps(i.attrs['State']), image_id=i.image.id,
                mounts=str(i.attrs['Mounts']), short_image_id=i.short_id,
                config=json.dumps(i.attrs['Config']), network_config=json.dumps(i.attrs['NetworkSettings']),
                status=i.status
            ))
        db.session.commit()
        for k, v in copies.items():
            tmpxx = Images.query.filter_by(image_id=k).first()
            # print(k)
            tmpxx.counts = v
        db.session.commit()
        # print('11111111111')
        time.sleep(1)


class queryinstances(Resource):
    def get(self):
        cli.containers.list()
        return {'containers': '=================='.join([json.dumps(x.attrs) for x in cli.containers.list()])}

    def put(self, todo_id):
        return {'a': 'good'}


# api.add_resource(TodoSimple, '/<string:todo_id>')
api.add_resource(TodoSimple, '/init')
api.add_resource(queryinstances, '/queryinstances')
t_dae_mt = threading.Thread(target=dae_maintain_insx, args=(cli,))
t_dae_mt.start()
app.run(debug=True)
