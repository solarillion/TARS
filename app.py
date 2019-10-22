# Authors: Nanda H Krishna (https://github.com/nandahkrishna), Abhijith Ragav (https://github.com/abhijithragav)

import os
import requests
from flask import Flask, jsonify, render_template, request
from slacker import Slacker

app = Flask(__name__)
app.debug = True

slack_key = os.environ.get("SLACK_KEY")
slack = Slacker(slack_key)

@app.route("/", methods=["GET", "POST"])
def index():
	if request.method == "POST":
		requests.post(request.json["response_url"], json={"success": True})
		return jsonify({"success": True})
	if request.method == "GET":
		return render_template("index.html")

if __name__ == "__main__":
	app.run()
