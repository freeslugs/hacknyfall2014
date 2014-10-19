import requests
from flask import Flask, request
from flask.ext import restful


app = Flask(__name__)
api = restful.Api(app)

### USER GUI ###

@app.route('/')
def hello_world():
  return 'Hello World!'

@app.route('/instagram-redirect')
def instagram_callback():
  code = request.args['code']
  token = get_access_token_instagram(code)
  # pics = get_images_instagram(token)
  return token
  #images = get_images_instagram(token)
  #return images
  # save_token 
  # render gallery
  
  # pics = get_pics_instagram(token)


# client side auth 
# https://api.instagram.com/oauth/authorize/?client_id=96eea83eeeed431490a2997dcb597d22&redirect_uri=http://127.0.0.1:5000/instagram-redirect&response_type=code

def get_access_token_instagram(code):
	payload = {'client_id': '96eea83eeeed431490a2997dcb597d22', 'client_secret': 'd9a08fd300854c9e9da1a4fe2035db1b', 'grant_type': 'authorization_code', 'redirect_uri': 'http://127.0.0.1:5000/instagram-redirect', 'code':code}
	r = requests.post("https://api.instagram.com/oauth/access_token", data=payload)
	print r.json()
	access_token = r.json()['access_token']
	return access_token

def get_images_instagram(access_token):
	r = requests.get("https://api.instagram.com/v1/users/self/media/recent?access_token="+access_token)
	images = r.json()
	array = []
	for image in images['data']:
		array.append(image['images']['standard_resolution']['url'])
	return array
	# return images['data'][0]['images']['standard_resolution']['url']
	# return images


### API ###

class Clarifai(restful.Resource):
  def get(self):
    token = clarifai_get_access_token()
    tags = clarifai_get_tags(token)
    return tags

class Instagram(restful.Resource):
  def get(self):
    return get_images_instagram("403542871.96eea83.6e3ef7b63c1e4ebf86ff2d171f856a33")

api.add_resource(Instagram, '/instagram')
api.add_resource(Clarifai, '/clarifai')




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
