# Authors: Nanda H Krishna (https://github.com/nandahkrishna), Abhijith Ragav (https://github.com/abhijithragav)

import os
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
	payload = request.json
	thread = threading.Thread(target=event_handler, args=(payload,))
	thread.start()
	return "", 200

def event_handler(payload):
	response_url = payload["response_url"]

@app.route("/interact", methods=["POST"])
def interact():
	payload = request.json
	slack.chat.post_message("UDD17R796", "Done")
	thread = threading.Thread(target=interact_handler, args=(payload,))
	thread.start()
	return "", 200

def interact_handler(payload):
	response_url = payload["response_url"]
	slack.chat.post_message("UDD17R796", respnse_url)
	if payload["actions"]["action_id"] == "enter_office_hours":
		requests.post(response_url, json=json.load("messages/office_hours_slot.json"))

if __name__ == "__main__":
	app.run()
