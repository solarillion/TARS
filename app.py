# Authors: Nanda H Krishna (https://github.com/nandahkrishna), Abhijith Ragav (https://github.com/abhijithragav)

import os
from flask import Flask, jsonify, render_template, request
from slacker import Slacker

app = Flask(__name__)
app.debug = True

@app.route("/", methods=["GET", "POST"])
def index():
	if request.method == "POST":
		slack_key = os.environ.get("SLACK_KEY")
		slack = Slacker(slack_key)
		slack.chat.post_message("#ta_group", "Meeting")
		challenge = request.json.get("challenge")
		return jsonify({"challenge": challenge})
	if request.method == "GET":
		return render_template("index.html")

if __name__ == "__main__":
	app.run()
