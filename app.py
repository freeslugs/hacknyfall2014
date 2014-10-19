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
  tag = StringField(max_length=55)
  prob = DecimalField(required=True)

class Image(db.Document):
  url = db.StringField(required=True)
  tags = ListField(ReferenceField(Tag))

class User(db.Document):
  name = db.StringField(required=True)
  user_id = db.StringField(required=True)
  token = db.StringField(required=True)
  images = ListField(ReferenceField(Image))

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

# class Clarifai(restful.Resource):
#   def get(self):
#     # request.form
#     # token = clarifai_get_access_token()
#     tags = clarifai_get_tags(clarifai_token)
#     return tags

# def get_clarifai():
#   token = clarifai_get_access_token()
#   tags = clarifai_get_tags(token)
#   return tags


# class ImageProcessing(restful.Resource):
#   def get(self):
#     user_id = request.args['user_id']
#     user = User.objects(user_id=user_id).first()
#     print user.images

#     return user
#     # get user by user_id
#     # for image in user:
#     #   get clarafai image url
#     #   save tags to img
    

#     # print get_clarifai()
    
#     # return "helloL"
    # 
class ImageProcessing(restful.Resource):
  def get(self):
    user_id = request.args['user_id']
    user = User.objects(user_id=user_id).first()
    if not user.images:
      get_images_instagram(user)
    
    for image in user.images:
      if not image.tags:
        clarifai_get_tags(image)

    # return json_util.dumps(user)
    # return {'data': user.images.to_json()}
    # print get_clarifai()
    test = user.images[0].tags[0].tag
    print test
    return test

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

def clarifai_get_tags(image, token=clarifai_token):
  url = image.url
  r = requests.get('https://api.clarifai.com/v1/tag/?url='+url+'&access_token='+token)
  data = r.json()['results'][0]['result']['tag']
  tags = data['classes']
  probs = data['probs']
  
  for i in xrange(0,len(tags)):
    tag = Tag(prob=probs[i], tag=tags[i])
    tag.save()
    image.tags.append(tag)
  image.save()
  
  return "success!"

if __name__ == '__main__':
	app.run()



# function for getting a code from user
# essentially user logins 
# we need to handle the callback
# extract the code
# use the code in another request ot get the acces token
# save that for a user
# use the token to make requests for pics
# 