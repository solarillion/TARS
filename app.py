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
import pyrebase

app = Flask(__name__)
app.debug = True

tars_admin = os.environ.get("TARS_ADMIN")
tars_token = os.environ.get("TARS_TOKEN")
tars_secret = os.environ.get("TARS_SECRET")
tars_bot_id = os.environ.get("TARS_BOT_ID")
general_id = os.environ.get("GENERAL_ID")
vineethv_id = os.environ.get("VINEETHV_ID")
firebase_api_key = os.environ.get("FIREBASE_API_KEY")
tars_fb_ad = os.environ.get("TARS_FB_AD")
tars_fb_url = os.environ.get("TARS_FB_URL")
tars_fb_sb = os.environ.get("TARS_FB_SB")

tars = slack.WebClient(token=tars_token)
slack_events_adapter = SlackEventAdapter(tars_secret, "/event", app)

vineethv_im_request = tars.im_open(user=vineethv_id)
vineethv_im_channel = vineethv_im_request.data["channel"]["id"]

config = {
  "apiKey": firebase_api_key,
  "authDomain": tars_fb_ad,
  "databaseURL": tars_fb_url,
  "storageBucket": tars_fb_sb
}
firebase = pyrebase.initialize_app(config)

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
        db = firebase.database()
        data = db.child("officehours").get().val()
        message = "Sir's office hours for the week:\n"
        for item in data[1:]:
            item["start"] = reformat_time(item["start"])
            item["end"] = reformat_time(item["end"])
            message += item["days"] + ": " + item["start"] + " - " + item["end"] + "\n"    
        tars.chat_postMessage(channel=general_id, text=message)

def reformat_time(ts):
    hour = int(ts.split(":")[0][-2:]) + 5
    min = int(ts.split(":")[1][:2]) + 22
    if min >= 60:
        min -= 60
        hour += 1
    time = ""
    if len(str(min)) == 1:
        min = "0" + str(min)
    if hour >= 12:
        if hour != 12:
            hour -= 12
        time = str(hour) + ":" + str(min) + " PM"
    else:
        time = str(hour) + ":" + str(min) + " AM"
    return time

if __name__ == "__main__":
    app.run()
