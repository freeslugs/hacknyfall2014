import requests
from flask import Flask, request
from flask.ext import restful
from flask.ext.mongoengine import *
from mongoengine import *
import json
# from bson import json_util

app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = {'DB': "hacknyfall2014"}
connect('hacknyfall2014', host='mongodb://columbia:giladabc@ds047040.mongolab.com:47040/hacknyfall2014')
api = restful.Api(app)
db = MongoEngine(app)
app.debug = True

clarifai_token = "IudTqeJRSFLpTl3Dj0nPgPP6AVsLeS"

class Tag(db.Document):
  tag_id = StringField(required=True)
  prob = DecimalField(required=True)

class Coordinate(db.Document):
  tag_id = StringField(required=True)
  prob = DecimalField(required=True)

class Image(db.Document):
  url = db.StringField(required=True)
  tags = ListField(ReferenceField(Tag))

class User(db.Document):
  name = db.StringField(required=True)
  user_id = db.StringField(required=True)
  token = db.StringField(required=True)
  images = ListField(ReferenceField(Image))
  coordinates = ListField(ReferenceField(Coordinate))

class MasterTags(db.Document):
  tag = StringField(max_length=55)

### USER GUI ###

@app.route('/')
def hello_world():
  return 'Hello World!'

@app.route('/instagram-redirect')
def instagram_callback():
  code = request.args['code']
  data = get_user_info(code)

  user = User.objects(user_id=data['user_id']).first()
  if user:
    user.access_token = data['access_token']
  else: 
    user = User(
      name = data['name'],
      user_id = data['user_id'],
      token = data['access_token']
    )

  user.save()
  return user.user_id

# client side auth 
# https://api.instagram.com/oauth/authorize/?client_id=96eea83eeeed431490a2997dcb597d22&redirect_uri=http://127.0.0.1:5000/instagram-redirect&response_type=code

### API ###

class ImageProcessing(restful.Resource):
  def get(self):
    user_id = request.args['user_id']
    user = User.objects(user_id=user_id).first()
    # if not user.images:
    get_images_instagram(user)
    
    for image in user.images:
      if not image.tags:
        clarifai_get_tags(user, image)

    for tag_id in user.coordinates:
      user.coordinates[tag_id] = (user.coordinates[tag_id] / len(user.images))
    # return json_util.dumps(user)
    # return {'data': user.images.to_json()}
    # print get_clarifai()
    # test = user.images[0].tags[0].tag
    return "test"

# api.add_resource(Instagram, '/instagram')
# api.add_resource(Clarifai, '/clarifai')
api.add_resource(ImageProcessing, '/image-processing')


def get_user_info(code):
  payload = {'client_id': '96eea83eeeed431490a2997dcb597d22', 'client_secret': 'd9a08fd300854c9e9da1a4fe2035db1b', 'grant_type': 'authorization_code', 'redirect_uri': 'http://127.0.0.1:5000/instagram-redirect', 'code':code}
  r = requests.post("https://api.instagram.com/oauth/access_token", data=payload)
  data = r.json()
  access_token = data['access_token']
  user_id = data['user']['id']
  name = data['user']['full_name']
  return {'access_token': access_token, 'user_id': user_id, 'name': name}

def get_images_instagram(user):
  access_token = user.token
  r = requests.get("https://api.instagram.com/v1/users/self/media/recent?access_token="+access_token)
  images = r.json()
  for image in images['data']:
    img = Image(url=image['images']['standard_resolution']['url'])
    img.save()
    user.images.append(img)
    user.save()

def clarifai_get_access_token():
	r = requests.post("https://api.clarifai.com/v1/token/?grant_type=client_credentials&client_id=urXuu-oV3NBj4WL8WUW37cPWlc1qDImDndJeDCc-&client_secret=LVqjz3Jhjb3xrM1IktglejjXLHZ-9e5QLJknvZAQ")
	access_token = r.json()['access_token']
	return access_token

def clarifai_get_tags(user, image, token=clarifai_token):
  url = image.url
  r = requests.get('https://api.clarifai.com/v1/tag/?url='+url+'&access_token='+token)
  data = r.json()['results'][0]['result']['tag']
  tags = data['classes']
  probs = data['probs']
  # rolling sum of probabbilities
  for i in xrange(0,len(tags)):
    # If tag already exists in huge list
    existing_tag = MasterTags.objects(tag=tags[i]).first()
    if existing_tag:
      tag = Tag(prob=probs[i], tag_id=str(existing_tag.id))
    else: 
      new_tag = MasterTags(tag=tags[i])
      new_tag.save()
      tag = Tag(prob=probs[i], tag_id=str(new_tag.id))
    tag.save()
    image.tags.append(tag)
    
    existing_coordinate = Coordinate()
    
    for c in user.coordinates:
      if c['tag_id'] == tag.tag_id:
        existing_coordinate = c

    # print existing_coordinate['prob']
    if existing_coordinate['prob']:
      existing_coordinate['prob'] += tag.prob
    else: 
      print tag.tag_id
      # user.coordinates.append({'tag_id': tag.tag_id, 'prob': tag.prob})
    
  print user.coordinates
  image.save()
  user.save()

  return "success!"

if __name__ == '__main__':
	app.run()
