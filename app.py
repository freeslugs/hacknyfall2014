import requests
from flask import Flask
from flask.ext import restful

app = Flask(__name__)
api = restful.Api(app)


class HelloWorld(restful.Resource):
  def get(self):
    token = get_access_token()
    tags = get_tags(token)
    return tags

api.add_resource(HelloWorld, '/')


def get_access_token():
	r = requests.post("https://api.clarifai.com/v1/token/?grant_type=client_credentials&client_id=urXuu-oV3NBj4WL8WUW37cPWlc1qDImDndJeDCc-&client_secret=LVqjz3Jhjb3xrM1IktglejjXLHZ-9e5QLJknvZAQ")
	access_token = r.json()['access_token']
	return access_token

def get_tags(token, url="http://www.clarifai.com/img/metro-north.jpg"):
	r = requests.get('https://api.clarifai.com/v1/tag/?url='+url+'&access_token='+token)
	return r.json()

if __name__ == '__main__':
	app.run()
