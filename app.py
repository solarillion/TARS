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
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

app = Flask(__name__)
app.debug = True

tars_admin = os.environ.get("TARS_ADMIN")
tars_token = os.environ.get("TARS_TOKEN")
tars_secret = os.environ.get("TARS_SECRET")
tars_bot_id = os.environ.get("TARS_BOT_ID")
vineethv_id = os.environ.get("VINEETHV_ID")
slack_google_credentials = os.environ.get("SLACK_GOOGLE_CREDENTIALS")

tars = slack.WebClient(token=tars_token)
slack_events_adapter = SlackEventAdapter(tars_secret, "/event", app)

vineethv_im_request = tars.im_open(user="UDD17R796")
vineethv_im_channel = vineethv_im_request.data["channel"]["id"]

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
slack_google_config = json.loads(slack_google_credentials)
flow = Flow.from_client_config(slack_google_config, SCOPES)
creds = flow.run_local_server(port=0)
service = build("sheets", "v4", credentials=creds)

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
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId="124rPdz4ouUjSFRKCaN5hwTHf3At53bxywZnjUz_q8iE", range="B2:D10").execute()
        values = result.get("values", [])
        message = ""
        for row in values:
            message.append(row[0] + " " + row[2] + "\n")
        tars.chat_postMessage(channel=vineethv_im_channel, text=message)

if __name__ == "__main__":
    app.run()
