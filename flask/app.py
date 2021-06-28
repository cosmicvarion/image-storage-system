from flask import Flask, request, jsonify, send_from_directory
from flask_mongoengine import MongoEngine
from celery import Celery
from PIL import Image
import uuid
import sys, os
import base64

app = Flask(__name__)

# mongo database
app.config['MONGODB_SETTINGS'] = {
    'db': 'flaskdb',
    'host': 'mongo_db',
    'port': 27017,
    'connect': False
}
db = MongoEngine(app)

class ImageEmbDoc(db.EmbeddedDocument):
    file_path  = db.StringField(required=True)
    timestamp  = db.StringField(required=True)
    store_name = db.StringField(required=True)
    camera_id  = db.StringField(required=True)
    barcode    = db.StringField(required=True)

class ImageBatch(db.Document):
    images = db.EmbeddedDocumentListField(ImageEmbDoc, default=[])

# celery
celery = Celery(
    app.name,
    backend = 'redis://redis:6379',
    broker  = 'redis://redis:6379',
)
celery.conf.update(app.config)
class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)
celery.Task = ContextTask

upload_folder = 'uploads'

@celery.task()
def store_image_batch(json_data):

    image_batch = ImageBatch()

    for image in json_data:

        # extract file
        file_path = os.path.join(upload_folder, f'{str(uuid.uuid4())}.jpg')
        with open(file_path, 'wb') as f:
            f.write(base64.b64decode(image['file'].encode('utf-8')))
        del image['file']

        # add to ImageBatch
        image['file_path'] = file_path
        im_doc = ImageEmbDoc(**image)
        image_batch.images.append(im_doc)

    image_batch.save()


# upload
@app.route('/upload_image_batch', methods=['POST'])
def upload_images():
    store_image_batch.delay(request.get_json())
    # store_image_batch(request.get_json())
    return jsonify({'success': True}), 200

# paginated retrieval
@app.route('/image_batches', methods=['GET'])
def image_batches():
    page     = int(request.args['page'])
    per_page = int(request.args['per_page'])
    return jsonify(ImageBatch.objects.paginate(page=page, per_page=per_page).items)

@app.route(f'/{upload_folder}/<file>', methods=['GET'])
def get_file(file):
    return send_from_directory(upload_folder, file, mimetype='image/jpeg')

if __name__ == '__main__':
    app.run()
