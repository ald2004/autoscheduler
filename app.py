from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
import docker
import json
import time
import tempfile
import subprocess
import threading
from typing import Union

app = Flask(__name__)
api = Api(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///autosche.sqlite"
db = SQLAlchemy(app)
TIME_FORMAT = '%Y%m%d%H%M%S'
LOG_FILE_DIR = './logs'
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
    compose_file = db.Column(db.Text)


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
        for image in cli.images.list(all=True):
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
                lifes=0, counts=0
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


def init_sqlalchemy():
    for image in cli.images.list(all=True):
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
            lifes=0, counts=0
        ))
    db.session.commit()


def start_ctn_compose(images: Images):
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', newline='\n') as fid:
            filename = fid.name
            fid.writelines(images.compose_file)
            fid.flush()
            a = subprocess.check_output(f"docker-compose -f {filename} up".split(), stderr=subprocess.STDOUT)
            return a.decode('utf-8')
    except:
        raise docker.errors.APIError


def stop_ctn_compose(images: Images):
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', newline='\n') as fid:
            filename = fid.name
            fid.writelines(images.compose_file)
            fid.flush()
            a = subprocess.check_output(f"docker-compose -f {filename} down".split(), stderr=subprocess.STDOUT)
            return a.decode('utf-8')
    except:
        raise docker.errors.APIError


def start_ctn_run(image: str, cmd: Union[str, list], **kwargs):
    try:
        ctn = cli.containers.run(image, auto_remove=True, command=cmd, remove=True, **kwargs)
        return ctn.logs()
    except:
        raise docker.errors.APIError


def dae_maintain_insx(cli: docker.client.DockerClient):
    while 1:
        copies = {"image_id": 0}  # 'sha256:76c152fbf...'
        copies = {}
        ins = cli.containers.list(all=True)
        for i in ins:
            if i.status.startswith('running'):  # running exited created
                copies[i.image.id] = copies.get(i.image.id) + 1 if copies.get(i.image.id) else 1
            else:
                copies[i.image.id] = 0
            db.session.merge(Instance(
                id=i.id, created=i.attrs['Created'],
                state=json.dumps(i.attrs['State']), image_id=i.image.id,
                mounts=str(i.attrs['Mounts']), short_image_id=i.short_id,
                config=json.dumps(i.attrs['Config']), network_config=json.dumps(i.attrs['NetworkSettings']),
                status=i.status
            ))
        db.session.commit()
        # print(copies)
        for k, v in copies.items():
            try:
                # print(f'k is {k},----------- v is {v}')
                tmpxx = Images.query.filter_by(image_id=k).first()
                # print(k)
                tmpxx.counts = v
            except Exception as e:
                print(k)
                raise e
        db.session.commit()

        # start stop containers according lives and counts.
        for k, v in copies.items():
            imagecount = Images.query.filter_by(image_id=k).first()
            if imagecount.lifes > imagecount.counts:
                # ctn=start_ctn_run(imagecount,detach=True,command="tail -f /dev/null")
                try:
                    logs = start_ctn_compose(imagecount)
                    print(f"the compose succeed start {imagecount.short_id[7:]} with logs : \n {logs}")
                except docker.errors.APIError:
                    print('xxxxxxxxxxx')
            elif imagecount.lifes < imagecount.counts:
                stop_ctn_compose(imagecount)
            ins = cli.containers.list()
            # ins.append(ctn)
            for i in ins:
                tmstp = time.strftime("TIME_FORMAT", time.localtime())
                with open(f'{LOG_FILE_DIR}/{imagecount.short_id}_{tmstp}.log', 'a') as fid:
                    fid.writelines(['\n'.join(list(x for x in i.logs()))])
                # print(imagecount.tags)
                # print('--------')
                # print(type(imagecount.tags))
                # print(f'imagecount.lifes is {imagecount.lifes}, and imagecount.counts is {imagecount.counts}')

                # start image by compose-file
                # cli.containers.run('',detach=True)
                # compose_file=imagecount.compose_file

            time.sleep(1)
        time.sleep(2)


class queryinstances(Resource):
    def get(self):
        return jsonify({'containers': '=================='.join([json.dumps(x.attrs) for x in cli.containers.list()])})

    def put(self, todo_id):
        return {'reason': 'not implemented'}


class queryinstancesfull(Resource):
    def get(self):
        return {'containers': ';'.join([json.dumps(x.attrs) for x in cli.containers.list(all=True)])}

    def put(self):
        return {'reason': 'not implemented'}


# import werkzeug.datastructures.ImmutableMultiDict
class addinstances(Resource):
    def get(self):
        return {'reason': 'not implemented'}

    def post(self):
        print(request.form['compose_fifle'])
        return jsonify(request.form)

    def put(self):
        try:
            data = json.loads(request.form['data'])
            tag = data.get('tag')
            image_id = data.get('image_id')
            lifes = data.get('lifes')
            compose_file = data.get('compose_file')
            if tag:
                tmpxx = Images.query.filter(Images.tags.contains(tag)).first()
            elif id:
                tmpxx = Images.query.filter_by(image_id=image_id).first()
            else:
                raise ValueError
            tmpxx.lifes = lifes
            tmpxx.compose_file = compose_file
            db.session.merge(tmpxx)
            db.session.commit()
            return jsonify({'code': 0,'message':f'tag {tag},image_id {image_id} succeed updated lifes {lifes}'})
        except Exception as e:
            msg = str(e)
            if isinstance(e, ValueError):
                msg += 'id or tag'
            return jsonify({'code':1,'message': f'some thing wrong: {msg}'})


class delinstances(Resource):
    def get(self):
        return {'reason': 'not implemented'}

    def put(self):
        pass

    def post(self):
        pass


# api.add_resource(TodoSimple, '/<string:todo_id>')
# api.add_resource(TodoSimple, '/init')
api.add_resource(queryinstances, '/queryinstances')
api.add_resource(queryinstancesfull, '/queryinstancesfull')
api.add_resource(addinstances, '/addinstances')
api.add_resource(delinstances, '/delinstances')
t_dae_mt = threading.Thread(target=dae_maintain_insx, args=(cli,))
t_dae_init = threading.Thread(target=init_sqlalchemy, args=())
t_dae_init.start()
t_dae_init.join()
t_dae_mt.start()
app.run(debug=True)
# t_dae_mt.join()
