# Authors: Nanda H Krishna (https://github.com/nandahkrishna), Abhijith Ragav (https://github.com/abhijithragav)

import os
import json
import requests
import threading
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
	payload = json.loads(request.form.get("payload"))
	thread = threading.Thread(target=event_handler, args=(payload,))
	thread.start()
	return "", 200

def event_handler(payload):
	response_url = payload["response_url"]

@app.route("/interact", methods=["POST"])
def interact():
	payload = json.loads(request.form.get("payload"))
	thread = threading.Thread(target=interact_handler, args=(payload,))
	thread.start()
	return "", 200

def interact_handler(payload):
	response_url = payload["response_url"]
	action_id = payload["actions"]["action_id"]
	headers = {"Content-type": "application/json"}
	slack.chat.post_message("UDD17R796", "1")
	if action_id == "enter_office_hours":
		slack.chat.post_message("UDD17R796", "2")
		requests.post(response_url, headers=headers, json=json.load(open("messages/office_hours_slot.json")))
	slack.chat.post_message("UDD17R96", "3")

if __name__ == "__main__":
	app.run()
