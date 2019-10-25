# Authors: Nanda H Krishna (https://github.com/nandahkrishna), Abhijith Ragav (https://github.com/abhijithragav)

import os
from datetime import *
import json
import requests
import threading
from flask import Flask, jsonify, render_template, request
from slacker import Slacker

app = Flask(__name__)
app.debug = True

vineethv_id = os.environ.get("VINEETHV_ID")
tars_admin = os.environ.get("TARS_ADMIN")
tars_token = os.environ.get("TARS_TOKEN")
tars = Slacker(tars_token)

post_headers = {"Content-type": "application/json", "Authorization": "Bearer " + tars_token}
response_headers = {"Content-type": "application/json"}

old_event = None

@app.route("/", methods=["GET"])
def index():
	return render_template("index.html")

@app.route("/event", methods=["POST"])
def event():
	payload = json.loads(request.get_data())
	thread = threading.Thread(target=event_handler, args=(payload,))
	thread.start()
	return "", 200

def event_handler(payload):
	try:
		text = payload["event"]["text"].replace("@", "")
		user = payload["event"]["user"]
		channel = payload["event"]["channel"]
		time = payload["event_time"]
		message = text + "\nFrom " + user + " in " + channel + "."
		tars.chat.post_message(tars_admin, message)
		text = text.lower()
		message = None
		if "request office hours" in text:
			if old_event is None or ("request office hours" in old_event["event"]["text"] and time - old_event["event_time"] >= 60):
				tars.chat.post_message("UDD17R796", "Office hours.")
				message = json.load(open("messages/request_office_hours.json"))
		if message is not None:
			requests.post(post_message, headers=post_headers, json=message)	
	except:
		message = json.dumps(payload).replace("@", "")
		tars.chat.post_message(tars_admin, message)
	finally:
		old_event = payload

@app.route("/interact", methods=["POST"])
def interact():
	payload = json.loads(request.form.get("payload"))
	thread = threading.Thread(target=interact_handler, args=(payload,))
	thread.start()
	return "", 200

def interact_handler(payload):
	headers = {"Content-type": "application/json"}
	response_url = payload["response_url"]
	action_id = payload["actions"][0]["action_id"]
	message = "Action " + action_id + "done."
	tars.chat.post_message(tars_admin, message)
	message = None
	if action_id == "enter_office_hours":
		message = json.load(open("messages/office_hours_slot.json"))
	elif action_id == "cancel_office_hours":
		message = json.load(open("messages/cancel_office_hours.json"))
	elif action_id == "slot_done":
		message = json.load(open("messages/confirm_office_hours.json"))
	elif action_id == "done_office_hours":
		message = json.load(open("messages/done_office_hours.json"))
	if message is not None:
		requests.post(response_url, headers=response_headers, json=message)

if __name__ == "__main__":
	app.run()
