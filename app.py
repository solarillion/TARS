# Authors: Nanda H Krishna (https://github.com/nandahkrishna), Abhijith Ragav (https://github.com/abhijithragav)

import os
from datetime import *
import json
import requests
import threading
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
app.debug = True

vineethv_id = os.environ.get("VINEETHV_ID")
tars_admin = os.environ.get("TARS_ADMIN")
tars_token = os.environ.get("TARS_TOKEN")

post_message = "https://slack.com/api/chat.postMessage"
update_message = ""

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
	headers = {"Content-type": "application/json"}
	try:
		text = payload["event"]["text"].replace("@", "")
		user = payload["event"]["text"]
		channel = payload["event"]["channel"]
		time = payload["event_time"]
		message = {"token": tars_token, "channel": tars_admin, "text": text + "\nFrom " + user " in " + channel + "."}
		requests.post(post_message, headers=headers, json=message)
		text = text.lower()
		message = None
		if all(x in text for x in ["request", "office hours"]):
			if old_event is None or time - old_event["event_time"] >= 60:
				message = json.load(open("messages/request_office_hours.json"))
		if message is not None:
			requests.post(post_message, headers=headers, json=message)	
	except:
		message = json.dumps(payload).replace("@", "")
		requests.post(post_message, headers=headers, json=message)
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
	message = {"token": tars_token, "channel": tars_admin, "text": "Action " + action_id + "done."}
	requests.post(post_message, headers=headers, json=message)
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
		requests.post(response_url, headers=headers, json=message)

if __name__ == "__main__":
	app.run()
