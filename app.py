# Authors: Nanda H Krishna (https://github.com/nandahkrishna), Abhijith Ragav (https://github.com/abhijithragav)

import os
from flask import Flask, jsonify, request
import sqlite3
from slacker import Slacker
from credentials.keys import *

app = Flask(__name__)
app.debug = True

@app.route("/", methods=["GET", "POST"])
def index():
	if request.method == "POST":
		slack_key = keys["slack"]
		slack = Slacker(keys["slack"])
		slack.chat.post_message("#ta_group", "Meeting")
		return jsonify({"success": True})

if __name__ == "__main__":
	app.run(host="0.0.0.0", port="2252")
