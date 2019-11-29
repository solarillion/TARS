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

firebase_url = "https://tars-1574957739449.firebaseio.com/.json"

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
    if "request office hours" in text:
        tars.chat_postMessage(channel=vineethv_im_channel, text="Sir, please fill your office hours in this form: https://forms.gle/eMoayTXg5KJCata68")
    if "post office hours" in text:
        response = requests.get(firebase_url)
        response = dict(response)
        response = response[response.keys[0]]
        message = ""
        for item in response:
            message += item["days"] + item["start"] + item["end"] + "\n"    
        tars.chat_postMessage(channel=vineethv_im_channel, text=message)

if __name__ == "__main__":
    app.run()
