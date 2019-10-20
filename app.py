# Authors: Nanda H Krishna (https://github.com/nandahkrishna), Abhijith Ragav (https://github.com/abhijithragav)

import os
from flask import Flask, jsonify, request
from slacker import Slacker

app = Flask(__name__)
app.debug = True

@app.route("/", methods=["GET", "POST"])
def index():
	if request.method == "POST":
		slack_key = os.environ.get("SLACK_KEY")
		slack = Slacker(slack_key)
		slack.chat.post_message("#ta_group", "Meeting")
		return jsonify({"success": True})

if __name__ == "__main__":
	app.run()
