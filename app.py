# Authors: Nanda H Krishna (https://github.com/nandahkrishna), Abhijith Ragav (https://github.com/abhijithragav)

import os
import requests
from flask import Flask, jsonify, render_template, request
from slacker import Slacker

app = Flask(__name__)
app.debug = True

slack_key = os.environ.get("SLACK_KEY")
slack = Slacker(slack_key)

@app.route("/", methods=["GET"])
def index():
	return render_template("index.html")

@app.route("/event", methods=["POST"])
def event():
	return jsonify({"success": True})

@app.route("/interact", methods=["POST"])
def interact():
	requests.post(request.json["response_url"], json={"success": True})
	return jsonify({"success": True})

if __name__ == "__main__":
	app.run()
