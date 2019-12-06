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
hyouka_fb_key = os.environ.get("HYOUKA_FB_KEY")
hyouka_fb_ad = os.environ.get("HYOUKA_FB_AD")
hyouka_fb_url = os.environ.get("HYOUKA_FB_URL")
hyouka_fb_sb = os.environ.get("HYOUKA_FB_SB")

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

hyouka_config = {
  "apiKey": hyouka_fb_key,
  "authDomain": hyouka_fb_ad,
  "databaseURL": hyouka_fb_url,
  "storageBucket": hyouka_fb_sb
}
hyouka_firebase = pyrebase.initialize_app(hyouka_config)

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
    db = firebase.database()
    if "request office hours" in text:
        tars.chat_postMessage(channel=vineethv_im_channel, text="Sir, please fill your office hours in this form: https://forms.gle/eMoayTXg5KJCata68")
    if "post office hours" in text:
        data = db.child("officehours").get().val()
        message = "Sir's office hours for the week:\n"
        for item in data[1:]:
            item["start"] = reformat_time(item["start"])
            item["end"] = reformat_time(item["end"])
            message += item["days"] + ": " + item["start"] + " - " + item["end"] + "\n"    
        tars.chat_postMessage(channel=general_id, text=message)
    if "add orientee" in text:
        ta = list(db.child("ta").get().val())
        if event_data["event"]["user"] not in ta:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You're not allowed to do this!")
            return
        words = text.split()[2:]
        slack_id = words[0].replace("@", "").upper()
        slack_id = slack_id.replace("<", "")
        slack_id = slack_id.replace(">", "")
        name = tars.users_info(user=slack_id).data["user"]["profile"]["real_name"]
        join = str(date.today())
        github = words[1]
        group = words[2].upper()
        db.child("orientee").child(slack_id).update({ "name": name, "join": join, "github": github, "group": group, "progress": "py1", "py_fin": "None", "g_fin": "None", "p_fin": "None"})
        hyouka_db = hyouka_firebase.database()
        hyouka_db.child(github).update({"name": name, "group": group, "progress": "py1", "slack": slack_id})
        tars.chat_postMessage(channel=event_data["event"]["channel"], text="Added orientee!")
    if "remove orientee" in text:
        ta = list(db.child("ta").get().val())
        if event_data["event"]["user"] not in ta:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You're not allowed to do this!")
            return
        slack_id = text.split()[2].replace("@", "").upper()
        slack_id = slack_id.replace("<", "")
        slack_id = slack_id.replace(">", "")
        github = db.child("orientee").child(slack_id).get().val()["github"]
        db.child("orientee").child(slack_id).remove()
        hyouka_db = hyouka_firebase.database()
        hyouka_db.child(github).remove()
        tars.chat_postMessage(channel=event_data["event"]["channel"], text="Removed from database. Also remove them from any orientee channels, and add them to research channels if required.")
    if "show orientee" in text:
        ta = list(db.child("ta").get().val())
        if event_data["event"]["user"] not in ta:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You're not allowed to do this!")
            return
        slack_id = text.split()[2].replace("@", "").upper()
        slack_id = slack_id.replace("<", "")
        slack_id = slack_id.replace(">", "")
        data = db.child("orientee").child(slack_id).get().val()
        message = "Progress of " + data["name"] + ":\nJoined: " + data["join"] + "\nGroup: " + data["group"] + "\nStatus: " + data["progress"]
        if data["py_fin"] != "None":
            message += "\nPython end: " + data["py_fin"]
        if data["g_fin"] != "None":
            message += "\nGroup end: " + data["g_fin"]
        if data["p_fin"] != "None":
            message += "\nProject end: " + data["p_fin"] + "\nAfter the project review, don't forget to remove orientee."
        tars.chat_postMessage(channel=event_data["event"]["channel"], text=message)
    if "verify orientee" in text:
        ta = list(db.child("ta").get().val())
        if event_data["event"]["user"] not in ta:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You're not allowed to do this!")
            return
        slack_id = text.split()[2].replace("@", "").upper()
        slack_id = slack_id.replace("<", "")
        slack_id = slack_id.replace(">", "")
        data = db.child("orientee").child(slack_id).get().val()
        status = data["progress"]
        github = data["github"]
        message = "Current status: " + status
        tars.chat_postMessage(channel=event_data["event"]["channel"], text=message)
        new_status = {"py2": "py3", "py3": data["group"].lower() + "1", "ml1": "ml2", "ml2": "ml3", "ml3": "mlp", "iot1": "iot2", "iot2": "iot3", "iot3": "iotp", "mg1": "mg2", "mg2": "mg3", "mg3": "mgp"}
        if "p" != status[-1]:
            db.child("orientee").child(slack_id).update({"progress": new_status[status]})
            hyouka_db.child(github).update({"progress": new_status[status]})
            if "1" in new_status[status]:
                db.child("orientee").child(slack_id).update({"py_fin": date.today()})
            elif "p" in new_status[status]:
                db.child("orientee").child(slack_id).update({"g_fin":str( date.today())})
        else:
            db.child("orientee").child(slack_id).update({"progress": "done"})
            db.child("orientee").child(slack_id).update({"p_fin": str(date.today())})
            hyouka_db.child(github).update({"progress": "done"})
        tars.chat_postMessage(channel=event_data["event"]["channel"], text="Verified!")

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
