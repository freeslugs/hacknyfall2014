import requests
from flask import Flask, request
from flask.ext import restful
from flask.ext.mongoengine import *
from mongoengine import *
import json
import sys, math
from flask.ext.cors import CORS, cross_origin

app = Flask(__name__, static_url_path='static')
app.config["MONGODB_SETTINGS"] = {'DB': "hacknyfall2014"}
connect('hacknyfall2014', host='mongodb://columbia:giladabc@ds047040.mongolab.com:47040/hacknyfall2014')
api = restful.Api(app)
cors = CORS(app)
db = MongoEngine(app)
app.debug = True

clarifai_token = "IudTqeJRSFLpTl3Dj0nPgPP6AVsLeS"

class Tag(db.Document):
  tag_id = StringField(required=True)
  prob = DecimalField(required=True, precision=10)

class Coordinate(db.Document):
  tag_id = StringField(required=True)
  prob = DecimalField(required=True, precision=10)

class Image(db.Document):
  url = db.StringField(required=True)
  tags = ListField(ReferenceField(Tag))
  gallery = StringField(required=True)

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
  return app.send_static_file('index.html')

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
# https://api.instagram.com/oauth/authorize/?client_id=96eea83eeeed431490a2997dcb597d22&redirect_uri=http://giladscoolapp.herokuapp.com/instagram-redirect&response_type=code

### API ###
#
#
class Exploration(restful.Resource):
  def get(self):
    the_id = request.args['id']
    status = request.args['status']
    visited = request.args['visited']
    # return user.user_id
    if status=="gallery":
      nearest_gal=nearest_gallery(User.objects(user_id=the_id).first(),visited)
      return nearest_gal.user_id
    else:
      image=Image.objects(id=the_id).first()
      nearest_img = nearest_image(image,visited)
      return str(nearest_img.id)
    # location=
    # status='gallery' # or 'image'

def nearest_gallery(current_gal,visited):
  galleries = User.objects()
  # visited (from front end)
  min_dist = sys.maxint

  for gallery in galleries:
    # print gallery
    if gallery != current_gal and gallery.user_id not in visited:
      # visited here? 
      next_coord = gallery['coordinates']
      # print next_coord
      dist=distance(current_gal['coordinates'], next_coord)
      if dist<distance:
        min_dist=dist
        next_gal=gallery        
  return next_gal

def locate_image(img):
  coordinates=[]
  for t in img['tags']:
      coordinates.append(t)
  return coordinates

def nearest_image(curr_img, visited):
  curr_loc=locate_image(curr_img)
  images=Image.objects()
  min_dist = sys.maxint
  for img in images:
    if img != curr_img and str(img.id) not in visited: #visited
      next_loc=locate_image(img)
      dist=distance(curr_loc,next_loc)
      if dist<min_dist:
        min_dist=dist
        next_img=img
  return next_img
        

def distance(curr, nxt):
  distance=0
  done=False
  for c in curr:
    curr_id=c['tag_id']
    for n in nxt:
      if curr_id == n['tag_id']:
        distance += (c['prob']-n['prob'])**2
        done = True
        break
    if done == False:
      distance+=(c['prob'])**2
    done=False
 
  for n in nxt:
    nxt_id = n['tag_id']
    for c in curr:
      if nxt_id==c['tag_id']:
        done=True
    if done==False:
      distance+=n['prob']**2
    done=False
  return math.sqrt(distance)



class ImageProcessing(restful.Resource):
  def get(self):
    user_id = request.args['user_id']
    user = User.objects(user_id=user_id).first()
    
    if len(user.coordinates) == 0:      
      get_images_instagram(user)
      for image in user.images:
        clarifai_get_tags(user, image)
      for c in user.coordinates:
        c['prob'] = c['prob'] / len(user.images)
    
    print len(user.coordinates)

    images = []
    for image in user.images:
      img = { 'url': image['url'], 'id': str(image['id']) }
      images.append(img)
      # image_id = image['$id']
    # return json_util.dumps(user)
    # return {'data': user.images.to_json()}
    # print get_clarifai()
    # test = user.images[0].tags[0].tag
    return {'data' : images}


api.add_resource(ImageProcessing, '/image-processing')
api.add_resource(Exploration, '/exploration')


def get_user_info(code):
  payload = {'client_id': '96eea83eeeed431490a2997dcb597d22', 'client_secret': 'd9a08fd300854c9e9da1a4fe2035db1b', 'grant_type': 'authorization_code', 'redirect_uri': 'http://giladscoolapp.herokuapp.com/instagram-redirect', 'code':code}
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
    img = Image(gallery=user['user_id'],url=image['images']['standard_resolution']['url'])
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
    
    print "saving new tag"
    tag.save()
    image.tags.append(tag)
    
    existing_coordinate = Coordinate()
    
    for c in user.coordinates:
      if c['tag_id'] == tag.tag_id:
        existing_coordinate = c

    if existing_coordinate['prob']:
      print existing_coordinate['tag_id'], existing_coordinate['prob']
      existing_coordinate['prob'] += tag.prob
      print existing_coordinate['tag_id'], existing_coordinate['prob']
    else: 
      c = Coordinate(tag_id=tag.tag_id, prob=tag.prob)
      c.save()
      user.coordinates.append(c)
    
  image.save()
  user.save()

  return "success!"



if __name__ == '__main__':
	app.run()
