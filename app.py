# Authors: Nanda H Krishna (https://github.com/nandahkrishna), Abhijith Ragav (https://github.com/abhijithragav)

import os
from datetime import *
from dateutil.relativedelta import *
from dateutil.rrule import *
import json
import requests
import threading
from flask import Flask, jsonify, render_template, request
import slack
from slackeventsapi import SlackEventAdapter

app = Flask(__name__)
app.debug = True

tars_admin = os.environ.get("TARS_ADMIN")
tars_token = os.environ.get("TARS_TOKEN")
tars_secret = os.environ.get("TARS_SECRET")
tars_bot_id = os.environ.get("TARS_BOT_ID")
vineethv_id = os.environ.get("VINEETHV_ID")

tars = slack.WebClient(token=tars_token)
slack_events_adapter = SlackEventAdapter(tars_secret, "/event", app)

vineethv_im_request = tars.im_open(user="UDD17R796")
vineethv_im_channel = vineethv_im_request.data["channel"]["id"]

response_headers = {"Content-type": "application/json"}

office_hours_messages = []
time_values = []

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@slack_events_adapter.on("message")
def message(event_data):
    thread = threading.Thread(target=im_event_handler, args=(event_data,))
    thread.start()
    return "", 200

def im_event_handler(event_data):
    text = event_data["event"]["text"].lower()
    if "schedule office hours" in text:
        schedule_office_hours_event_handler()
            
def schedule_office_hours_event_handler():
    office_hours_messages.clear()
    message = json.load(open("messages/request_office_hours.json"))
    tars.chat_postMessage(channel=vineethv_im_channel, text=message["text"], blocks=message["blocks"])
        
@app.route("/interact", methods=["POST"])
def interact():
    payload = json.loads(request.form.get("payload"))
    thread = threading.Thread(target=interact_handler, args=(payload,))
    thread.start()
    return "", 200
    
def interact_handler(payload):
    action_id = payload["actions"][0]["action_id"]
    if "office_hours" in action_id:
        office_hours_interact_handler(action_id, payload)

def office_hours_interact_handler(action_id, payload):
    message = None
    if action_id == "enter_office_hours":
        text = "Your slot details will be updated here."
        office_hours_messages.insert(0, tars.chat_postMessage(channel=vineethv_im_channel, text=text).data)
        message = json.load(open("messages/slot_office_hours.json"))
    elif action_id == "cancel_office_hours":
        message = json.load(open("messages/cancel_office_hours.json"))
    elif action_id == "select_days_office_hours":
        options = payload["actions"][0]["selected_options"]
        text = ""
        for option in options:
            text += option["text"]["text"] + " "
        details = office_hours_messages.pop(0)
        ts = details["ts"]
        office_hours_messages.insert(0, tars.chat_update(as_user=True, channel=vineethv_im_channel, ts=ts, text=text).data)
    elif action_id == "select_start_time_office_hours":
        time_values.clear()
        time_values.append(payload["actions"][0]["selected_option"]["value"])
        time_values.append("")
        start = payload["actions"][0]["selected_option"]["text"]["text"] + " - "
        details = office_hours_messages.pop(0)
        ts = details["ts"]
        text = details["message"]["text"]
        text += start
        office_hours_messages.insert(0, tars.chat_update(as_user=True, channel=vineethv_im_channel, ts=ts, text=text).data)
    elif action_id == "select_end_time_office_hours":
        time_values.pop(1)
        time_values.insert(1, payload["actions"][0]["selected_option"]["value"])
        end = payload["actions"][0]["selected_option"]["text"]["text"] + "\n"
        details = office_hours_messages.pop(0)
        ts = details["ts"]
        text = details["text"]
        text += end
        office_hours_messages.insert(0, tars.chat_update(as_user=True, channel=vineethv_im_channel, ts=ts, text=text).data)
    elif action_id == "slot_done_office_hours":
        if datetime.strptime(time_values[0], "%H:%M").time() > datetime.strptime(time_values[1], "%H:%M").time():
            message = json.load(open("messages/confirm_office_hours.json"))
        else:
            details = office_hours_messages.pop(0)
            ts = details["ts"]
            text = details["text"]
            text += "Invalid!"
            office_hours_messages.insert(0, tars.chat_update(as_user=True, channel=vineethv_im_channel, ts=ts, text=text).data)
    elif action_id == "done_office_hours":
        message = json.load(open("messages/done_office_hours.json"))
        text = ""
        for m in office_hours_messages:
            text += m["message"]["text"]
        tars.chat_postMessage(channel=tars_admin, text=text)
    if message is not None:
        message["channel"] = vineethv_im_channel
        response_url = payload["response_url"]
        requests.post(response_url, headers=response_headers, json=message)

if __name__ == "__main__":
    app.run()
