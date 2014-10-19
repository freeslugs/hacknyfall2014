import requests
from flask import Flask, request
from flask.ext import restful
from flask.ext.mongoengine import MongoEngine
from mongoengine import connect

app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = {'DB': "hacknyfall2014"}
connect('hacknyfall2014', host='mongodb://columbia:giladabc@ds047040.mongolab.com:47040/hacknyfall2014')
api = restful.Api(app)
db = MongoEngine(app)

### USER GUI ###

@app.route('/')
def hello_world():
  return 'Hello World!'

@app.route('/instagram-redirect')
def instagram_callback():
  code = request.args['code']
  token = get_access_token_instagram(code)
  return token
  # save_token 
  # render gallery
  
  # pics = get_pics_instagram(token)


# client side auth 
# https://api.instagram.com/oauth/authorize/?client_id=96eea83eeeed431490a2997dcb597d22&redirect_uri=http://127.0.0.1:5000/instagram-redirect&response_type=code

def get_access_token_instagram(code):
	payload = {'client_id': '96eea83eeeed431490a2997dcb597d22', 'client_secret': 'd9a08fd300854c9e9da1a4fe2035db1b', 'grant_type': 'authorization_code', 'redirect_uri': 'http://127.0.0.1:5000/instagram-redirect', 'code':code}
	r = requests.post("https://api.instagram.com/oauth/access_token", data=payload)
	access_token = r.json()['access_token']
	return access_token


### API ###

class Clarifai(restful.Resource):
  def get(self):
    token = clarifai_get_access_token()
    tags = clarifai_get_tags(token)
    return tags

def get_clarifai():
    token = clarifai_get_access_token()
    tags = clarifai_get_tags(token)
    return tags


class ImageProcessing(restful.Resource):
  def get(self):
      print get_clarifai()
      return "helloL"

api.add_resource(Clarifai, '/clarifai')
api.add_resource(ImageProcessing, '/image-process')




# function for getting a code from user
# essentially user logins 
# we need to handle the callback
# extract the code
# use the code in another request ot get the acces token
# save that for a user
# use the token to make requests for pics
# 

def clarifai_get_access_token():
	r = requests.post("https://api.clarifai.com/v1/token/?grant_type=client_credentials&client_id=urXuu-oV3NBj4WL8WUW37cPWlc1qDImDndJeDCc-&client_secret=LVqjz3Jhjb3xrM1IktglejjXLHZ-9e5QLJknvZAQ")
	access_token = r.json()['access_token']
	return access_token

def clarifai_get_tags(token, url="http://www.clarifai.com/img/metro-north.jpg"):
	r = requests.get('https://api.clarifai.com/v1/tag/?url='+url+'&access_token='+token)
	return r.json()


def parse_instagram_callback(code):
  return "hello"

if __name__ == '__main__':
	app.run()
