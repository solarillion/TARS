# -*- coding: utf-8 -*-
# Authors: Nanda H Krishna (https://github.com/nandahkrishna), Naveen Narayanan (https://github.com/naveenggmu), Mahesh Bharadwaj (https://github.com/MaheshBharadwaj)

import bcrypt
from datetime import *
from dateutil.relativedelta import *
from dateutil.rrule import *
from flask import Flask, jsonify, redirect, request, render_template, redirect, url_for
import flask_login
import git
from git import Repo
from github import Github
import json
import os
import pyrebase
import requests
import slack
from slackeventsapi import SlackEventAdapter
import shutil
import shlex
import time
import threading
from urllib.parse import parse_qs
from werkzeug.utils import secure_filename
import yaml
from yaml import load, dump

tars_token = os.environ.get("TARS_TOKEN")
tars_user_token = os.environ.get("TARS_USER_TOKEN")
tars_admin = os.environ.get("TARS_ADMIN")
tars_secret = os.environ.get("TARS_SECRET")
tars_bot_id = os.environ.get("TARS_BOT_ID")
tars_id = os.environ.get("TARS_ID")
general_id = os.environ.get("GENERAL_ID")
orientation_id = os.environ.get("ORIENTATION_ID")
project_id = os.environ.get("PROJECT_ID")
sf_research = os.environ.get("SF_RESEARCH")
sf_ta = os.environ.get("SF_TA")
vineethv_id = os.environ.get("VINEETHV_ID")
office_hours_form = os.environ.get("OFFICE_HOURS_FORM")
firebase_api_key = os.environ.get("FIREBASE_API_KEY")
tars_fb_ad = os.environ.get("TARS_FB_AD")
tars_fb_url = os.environ.get("TARS_FB_URL")
tars_fb_sb = os.environ.get("TARS_FB_SB")
key_fb_tars = os.environ.get("KEY_FB_TARS")
hyouka_fb_key = os.environ.get("HYOUKA_FB_KEY")
hyouka_fb_ad = os.environ.get("HYOUKA_FB_AD")
hyouka_fb_url = os.environ.get("HYOUKA_FB_URL")
hyouka_fb_sb = os.environ.get("HYOUKA_FB_SB")
key_fb_hyouka = os.environ.get("KEY_FB_HYOUKA")
github_secret = os.environ.get("GITHUB_SECRET")
username = os.environ.get("USERNAME")
password = os.environ.get("PASSWORD").encode()
github_username = os.environ.get("GITHUB_USERNAME")
github_email = os.environ.get("GITHUB_EMAIL")
github_password = os.environ.get("GITHUB_ACCESS_TOKEN")
secret = os.environ.get("SECRET")

app = Flask(__name__)
app.secret_key = secret
app.debug = True

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def load_user(id):
    if id != username:
        return
    user = User()
    user.id = id
    return user

tars = slack.WebClient(token=tars_token)
tars_user = slack.WebClient(token=tars_user_token)
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
db = firebase.database()

hyouka_config = {
  "apiKey": hyouka_fb_key,
  "authDomain": hyouka_fb_ad,
  "databaseURL": hyouka_fb_url,
  "storageBucket": hyouka_fb_sb
}
hyouka_firebase = pyrebase.initialize_app(hyouka_config)
hyouka_db = hyouka_firebase.database()

@app.route("/", methods=["GET"])
def index():
    return redirect("https://solarillionfoundation.org/projects/TARS")

@slack_events_adapter.on("message")
def message(event_data):
    thread = threading.Thread(target=im_event_handler, args=(event_data,))
    thread.start()
    return "OK", 200

def im_event_handler(event_data):
    texto = event_data["event"]["text"]
    text = event_data["event"]["text"].lower()
    if "request office hours" in text:
        admin = list(db.child(key_fb_tars).child("admin").get().val())
        if event_data["event"]["user"] not in admin:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You're not allowed to do this!")
            return
        tars.chat_postMessage(channel=vineethv_im_channel, text="Sir, please fill your office hours in this form: https://forms.gle/eMoayTXg5KJCata68")
    elif "remind office hours" in text:
        admin = list(db.child(key_fb_tars).child("admin").get().val())
        if event_data["event"]["user"] not in admin:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You're not allowed to do this!")
            return
        tars.chat_postMessage(channel=vineethv_im_channel, text="Sir, if you haven't filled your office hours yet, please do so by 9 pm tonight. Here's the link to the form: " + office_hours_form)
    elif "post office hours" in text:
        admin = list(db.child(key_fb_tars).child("admin").get().val())
        if event_data["event"]["user"] not in admin:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You're not allowed to do this!")
            return
        data = db.child(key_fb_tars).child("officehours").get().val()
        message = "Sir's office hours for the week:\n"
        for item in data[1:]:
            item["start"] = reformat_time(item["start"])
            item["end"] = reformat_time(item["end"])
            message += item["days"] + ": " + item["start"] + " - " + item["end"] + "\n"    
        tars.chat_postMessage(channel=general_id, text=message)
    elif "add orientee" in text:
        ta = list(db.child(key_fb_tars).child("ta").get().val())
        orientees = list(db.child(key_fb_tars).child("orientee").get().val())
        if event_data["event"]["user"] not in ta:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You're not allowed to do this!")
            return
        words = text.split()[2:]
        slack_id = words[0].replace("@", "").upper()
        slack_id = slack_id.replace("<", "")
        slack_id = slack_id.replace(">", "")
        if slack_id in orientees:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="Already added!")
            return
        name = tars.users_info(user=slack_id).data["user"]["profile"]["real_name"]
        join = date.today()
        github = words[1]
        if github == "none":
            db.child(key_fb_tars).child("orientee").child(slack_id).update({"name": name, "join": "None", "github": slack_id + "nogithub", "group": "None", "progress": "None", "pyd": "None", "py1_d": "None", "py1_fin": "None", "py2_d": "None", "py2_fin": "None", "py3_d": "None", "py3_fin": "None", "gd": "None", "g1_d": "None", "g1_fin": "None", "g2_d": "None", "g2_fin": "None", "g3_d": "None", "g3_fin": "None", "pd": "None", "p_d": "None", "p_fin": "None"})
            hyouka_db.child(key_fb_hyouka).child(slack_id + "nogithub").update({"name": name, "group": "None", "progress": "None", "slack": slack_id})
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="Added orientee with all None. Update Firebase.")
            return
        group = words[2].upper()
        if "O" in group:
            group = "IoT"
        py_duration = int(words[3])
        delta = timedelta(py_duration)
        g_delta = timedelta(14)
        p_delta = timedelta(60)
        db.child(key_fb_tars).child("orientee").child(slack_id).update({"name": name, "join": str(join), "github": github, "group": group, "progress": "py1", "pyd": str(py_duration), "py1_d": str(join + delta), "py1_fin": "None", "py2_d": str(join + 2 * delta), "py2_fin": "None", "py3_d": str(join + 3 * delta), "py3_fin": "None", "gd": "14", "g1_d": str(join + 3 * delta + g_delta), "g1_fin": "None", "g2_d": str(join + 3 * delta + 2 * g_delta), "g2_fin": "None", "g3_d": str(join + 3 * delta + 3 * g_delta), "g3_fin": "None", "pd": "60", "p_d": str(join + 3 * delta + 3 * g_delta + p_delta), "p_fin": "None"})
        hyouka_db.child(key_fb_hyouka).child(github).update({"name": name, "group": group, "progress": "py1", "slack": slack_id})
        tars.chat_postMessage(channel=event_data["event"]["channel"], text="Added orientee!")
    elif "remove orientee" in text:
        ta = list(db.child(key_fb_tars).child("ta").get().val())
        if event_data["event"]["user"] not in ta:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You're not allowed to do this!")
            return
        slack_id = text.split()[2].replace("@", "").upper()
        slack_id = slack_id.replace("<", "")
        slack_id = slack_id.replace(">", "")
        github = db.child(key_fb_tars).child("orientee").child(slack_id).get().val()["github"]
        db.child(key_fb_tars).child("orientee").child(slack_id).remove()
        hyouka_db.child(key_fb_hyouka).child(github).remove()
        tars.chat_postMessage(channel=event_data["event"]["channel"], text="Removed from database.")
    elif "show orientee" in text:
        ta = list(db.child(key_fb_tars).child("ta").get().val())
        if event_data["event"]["user"] not in ta:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You're not allowed to do this!")
            return
        slack_id = text.split()[2].replace("@", "").upper()
        slack_id = slack_id.replace("<", "")
        slack_id = slack_id.replace(">", "")
        today = date.today()
        deadline = None
        data = db.child(key_fb_tars).child("orientee").child(slack_id).get().val()
        message = "Progress of " + data["name"] + ":\nJoined: " + data["join"] + "\nGroup: " + data["group"] + "\nStatus: " + data["progress"] + "\n*Report:*\n"
        if data["py1_d"] != "None":
            message += "Python duration: " + data["pyd"] + "\nPython 1 deadline: " + data["py1_d"]
            deadline = date.fromisoformat(data["py1_d"])
        if data["py1_fin"] != "None":
            message += "\nPython 1 end: " + data["py1_fin"] + "\nPython 2 deadline: " + data["py2_d"]
            deadline = date.fromisoformat(data["py2_d"])
        if data["py2_fin"] != "None":
            message += "\nPython 2 end: " + data["py2_fin"] + "\nPython 3 deadline: " + data["py3_d"]
            deadline = date.fromisoformat(data["py3_d"])
        if data["py3_fin"] != "None":
            message += "\nPython 3 end: " + data["py3_fin"] + "\nGroup duration: " + data["gd"] + "\nGroup 1 deadline: " + data["g1_d"]
            deadline = date.fromisoformat(data["g1_d"])
        if data["g1_fin"] != "None":
            message += "\nGroup 1 end: " + data["g1_fin"] + "\nGroup 2 deadline: " + data["g2_d"]
            deadline = date.fromisoformat(data["g2_d"])
        if data["g2_fin"] != "None":
            message += "\nGroup 2 end: " + data["g2_fin"] + "\nGroup 3 deadline: " + data["g3_d"]
            deadline = date.fromisoformat(data["g3_d"])
        if data["g3_fin"] != "None":
            message += "\nGroup 3 end: " + data["g3_fin"] + "\nProject duration: " + data["pd"] + "\nProject deadline: " + data["p_d"]
            deadline = date.fromisoformat(data["p_d"])
        if data["p_fin"] != "None":
            message += "\nProject end: " + data["p_fin"] + "\nAfter the project review, don't forget to remove orientee."
            deadline = None
        if deadline is not None:
            delta = deadline - today
            if delta.days < 0:
                message += "\nLagging by " + str(-delta.days) + " days(s)"
            else:
                message += "\nOn track"
        tars.chat_postMessage(channel=event_data["event"]["channel"], text=message)
    elif "track all orientee" in text:
        ta = list(db.child(key_fb_tars).child("ta").get().val())
        if event_data["event"]["user"] not in ta:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You're not allowed to do this!")
            return
        today = date.today()
        data = db.child(key_fb_tars).child("orientee").get().val()
        data.pop("-", None)
        message = "*Orientee Progress Tracker:*\n"
        for slack in data.keys():
            orientee = data[slack]
            message += "\n<@" + slack + "> - " + orientee["progress"]
            if orientee["progress"] != "done":
                if "py" in orientee["progress"]:
                    deadline = orientee["progress"] + "_d"
                    deadline = orientee[deadline]
                    message += "\nDeadline: " + deadline
                    deadline = date.fromisoformat(deadline)
                    delta = deadline - today
                    if delta.days < 0:
                        message += "\nLagging by " + str(-delta.days) + " day(s)"
                    else:
                        message += "\nOn track"
                elif orientee["progress"][-1] != "p":
                    deadline = "g" + orientee["progress"][-1] + "_d"
                    deadline = orientee[deadline]
                    message += "\nDeadline: " + deadline
                    deadline = date.fromisoformat(deadline)
                    delta = deadline - today
                    if delta.days < 0:
                        message += "\nLagging by " + str(-delta.days) + " day(s)"
                    else:
                        message += "\nOn track"
                else:
                    deadline = orientee["p_d"]
                    message += "\nDeadline: " + deadline
                    deadline = date.fromisoformat(deadline)
                    delta = deadline - today
                    if delta.days < 0:
                        message += "\nLagging by " + str(-delta.days) + " day(s)"
                    else:
                        message += "\nOn track"
            message += "\n"
        if len(data) == 0:
            message += "No orientees to track!"
        if "sf_ta" in text:
            tars.chat_postMessage(channel=sf_ta, text=message)
        else:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text=message)
    elif "verify orientee" in text:
        ta = list(db.child(key_fb_tars).child("ta").get().val())
        if event_data["event"]["user"] not in ta:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You're not allowed to do this!")
            return
        slack_id = text.split()[2].replace("@", "").upper()
        slack_id = slack_id.replace("<", "")
        slack_id = slack_id.replace(">", "")
        data = db.child(key_fb_tars).child("orientee").child(slack_id).get().val()
        status = data["progress"]
        github = data["github"]
        message = "Current status: " + status
        tars.chat_postMessage(channel=event_data["event"]["channel"], text=message)
        new_status = {"py1": "py2", "py2": "py3", "py3": data["group"].lower() + "1", "ml1": "ml2", "ml2": "ml3", "ml3": "mlp", "iot1": "iot2", "iot2": "iot3", "iot3": "iotp", "mg1": "mg2", "mg2": "mg3", "mg3": "mgp"}
        if status == "py1" or status == "py2" or status == "py3":
            hyouka_status = hyouka_db.child(key_fb_hyouka).child(github).get().val()["progress"]
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="Hyouka status: " + str(hyouka_status))
            db.child(key_fb_tars).child("orientee").child(slack_id).update({"progress": new_status[status]})
            hyouka_db.child(key_fb_hyouka).child(github).update({"progress": new_status[status]})
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="Verified " + status + "!")
            orientee = tars.im_open(user=slack_id).data["channel"]["id"]
            tars.chat_postMessage(channel=orientee, text="Verified " + status + "! Move on to " + new_status[status] + " now.")
            tars.chat_postMessage(channel=orientation_id, text="<@" + slack_id + "> has completed " + status + ", verified by <@" + event_data["event"]["user"] + ">.")
            db.child(key_fb_tars).child("orientee").child(slack_id).update({status + "_fin": str(date.today())})
        elif "p" != status[-1]:
            db.child(key_fb_tars).child("orientee").child(slack_id).update({"progress": new_status[status]})
            hyouka_db.child(key_fb_hyouka).child(github).update({"progress": new_status[status]})
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="Verified " + status + "!")
            orientee = tars.im_open(user=slack_id).data["channel"]["id"]
            tars.chat_postMessage(channel=orientee, text="Verified " + status + "! Move on to " + new_status[status] + " now.")
            tars.chat_postMessage(channel=orientation_id, text="<@" + slack_id + "> has completed " + status + ", verified by <@" + event_data["event"]["user"] + ">.")
            db.child(key_fb_tars).child("orientee").child(slack_id).update({"g" + status[-1] + "_fin":str( date.today())})
            if "3" in status:
                tars.chat_postMessage(channel=orientation_id, text="<@" + slack_id + "> has completed the assignments. Congrats!")
                tars_user.groups_kick(channel=orientation_id, user=slack_id)
                tars_user.groups_invite(channel=project_id, user=slack_id)
        else:
            db.child(key_fb_tars).child("orientee").child(slack_id).update({"progress": "done"})
            db.child(key_fb_tars).child("orientee").child(slack_id).update({"p_fin": str(date.today())})
            hyouka_db.child(key_fb_hyouka).child(github).update({"progress": "done"})
            tars.chat_postMessage(channel=project_id, text="<@" + slack_id + "> has completed the project. Congrats!")
            tars_user.groups_kick(channel=project_id, user=slack_id)
            tars_user.groups_invite(channel=sf_research, user=slack_id)
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="Verified! Project and reviews complete, added orientee to #sf_research.")
            orientee = tars.im_open(user=slack_id).data["channel"]["id"]
            message = "You have completed your project. Great work! Visit https://sf-tars.herokuapp.com/add-person to add yourself to the website."
            tars.chat_postMessage(channel=orientee, text=message)
            tars.chat_postMessage(channel=tars_admin, text="Added <@" + slack_id + "> to #sf_research, execute `remove orientee` later on.")
    elif "book meeting" in text:
        slack_id = event_data["event"]["user"]
        meetings = db.child(key_fb_tars).child("meetings").get().val()
        id = "0"
        if meetings is not None:
            for i in list(meetings):
                if slack_id in i:
                    id = i
        if id == "0":
            id = slack_id + "_1"
        else:
            n = str(int(id.split("_")[1]) + 1)
            id = slack_id + "_" + n
        lines = texto.split("\n")
        meeting = " ".join(lines[0].split(" ")[2:])
        people = [tars.users_info(user=slack_id).data["user"]["profile"]["email"]]
        people_slack = [slack_id, vineethv_id]
        if len(lines) == 2:
            add =  lines[1].replace("@", "").replace("<", "").replace(">", "").upper().split()
            people_slack += add
            add = list(map(lambda x: tars.users_info(user=x).data["user"]["profile"]["email"], add))
            people = people + add
        db.child(key_fb_tars).child("bookings").child(id).set({"meeting": meeting, "people": people, "people_slack": people_slack})
        tars.chat_postMessage(channel=event_data["event"]["channel"], text="The meeting has been booked!")
    elif "show meeting" in text:
        slack_id = event_data["event"]["user"]
        meetings = db.child(key_fb_tars).child("meetings").get().val()
        if meetings is not None:
            meetings = dict(meetings)
            count = 0
            keys = list(meetings.keys())
            for i in keys:
                if slack_id in i:
                    count += 1
                    item = db.child(key_fb_tars).child("meetings").child(i).get().val()
                    text = "`" + i.split("_")[1] + "`: " + item["desc"] + ", " + reformat_meeting_date(item["start"]) + " " + reformat_meeting_time(item["start"]) + " - " + reformat_meeting_time(item["end"])
                    if count == 1:
                        tars.chat_postMessage(channel=event_data["event"]["channel"], text="*Meetings you booked:*")
                    tars.chat_postMessage(channel=event_data["event"]["channel"], text=text)
                    meetings.pop(i)
            invites = 0
            keys = list(meetings.keys())
            for i in keys:
                if slack_id in list(meetings[i]["people"]):
                    invites += 1
                    item = db.child(key_fb_tars).child("meetings").child(i).get().val()
                    text = "`*`: " + item["desc"] + ", " + reformat_meeting_date(item["start"]) + " " + reformat_meeting_time(item["start"]) + " - " + reformat_meeting_time(item["end"])
                    if invites == 1:
                        tars.chat_postMessage(channel=event_data["event"]["channel"], text="*Meetings you've been invited to:*")
                    tars.chat_postMessage(channel=event_data["event"]["channel"], text=text)
                    meetings.pop(i)
            if count == 0 and invites == 0:
                tars.chat_postMessage(channel=event_data["event"]["channel"], text="You haven't booked or been invited to any meetings!")
    elif "cancel meeting" in text:
        slack_id = event_data["event"]["user"]
        meetings = db.child(key_fb_tars).child("meetings").get().val()
        if meetings is None:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You haven't booked any meetings!")
            return
        id = text.split(" ")[2]
        cancel = False
        for i in list(meetings):
            if slack_id in i and i.split("_")[1] == id:
                db.child(key_fb_tars).child("cancels").update({i: "cancel"})
                tars.chat_postMessage(channel=event_data["event"]["channel"], text="Alright, I'll cancel that one.")
                cancel = True
                break
        if not cancel:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="I couldn't find that meeting. Check again with `show meetings` and enter the correct meeting number.")
    elif "request ta hours" in text:
        admin = list(db.child(key_fb_tars).child("admin").get().val())
        if event_data["event"]["user"] not in admin:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You're not allowed to do this!")
            return
        message1 = tars_user.chat_postMessage(channel=sf_ta, text="<@" + tars_id + "> poll \"Mon-Thu TA Hours\" \"Monday 18:00-20:00\" \"Tuesday 18:00-20:00\" \"Wednesday 18:00-20:00\" \"Thursday 18:00-20:00\"", as_user=True)
        message2 = tars_user.chat_postMessage(channel=sf_ta, text="<@" + tars_id + "> poll \"Fri-Sun TA Hours\" \"Friday 18:00-20:00\" \"Saturday 13:00-15:00\" \"Saturday 16:00-18:00\" \"Saturday 18:00-20:00\" \"Sunday 10:30-13:00\" \"Sunday 13:30-16:00\" \"Sunday 16:30-19:00\"", as_user=True)
        time.sleep(3)
        tars_user.chat_delete(channel=sf_ta, ts=message1.data["ts"], as_user=True)
        tars_user.chat_delete(channel=sf_ta, ts=message2.data["ts"], as_user=True)
        tars.chat_postMessage(channel=sf_ta, text="Mark your hours by 18:00 on Sunday for Mon-Thu.")
        tars.chat_postMessage(channel=sf_ta, text="Mark your hours by 18:00 on Thursday for Fri-Sun.")
    elif "remind weekday ta hours" in text:
        admin = list(db.child(key_fb_tars).child("admin").get().val())
        if event_data["event"]["user"] not in admin:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You're not allowed to do this!")
            return
        tars.chat_postMessage(channel=sf_ta, text="Don't forget to mark your Mon-Thu TA Hours before 18:00, Sunday.")
    elif "remind weekend ta hours" in text:
        admin = list(db.child(key_fb_tars).child("admin").get().val())
        if event_data["event"]["user"] not in admin:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You're not allowed to do this!")
            return
        tars.chat_postMessage(channel=sf_ta, text="Don't forget to mark your Fri-Sun TA Hours before 18:00, Thursday.")
    elif "post weekday ta hours" in text:
        admin = list(db.child(key_fb_tars).child("admin").get().val())
        if event_data["event"]["user"] not in admin:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You're not allowed to do this!")
            return
        mon_thu_poll = db.child(key_fb_tars).child("tapoll").child("monthu").get().val()
        poll = db.child(key_fb_tars).child("polls").child(mon_thu_poll).get().val()
        db.child(key_fb_tars).child("polls").child(mon_thu_poll).remove()
        text = "TA Hours for Monday to Thursday:\n"
        for block in poll["message"][1:-3]:
            try:
                text += block["text"]["text"].split("`")[0].strip() + " " + block["text"]["text"].split("`")[2] + "\n"
            except:
                text += block["text"]["text"] + "\n"
        tars.chat_delete(channel=sf_ta, ts=mon_thu_poll.replace("-", "."))
        tars.chat_postMessage(channel=sf_ta, text=text)
        tars.chat_postMessage(channel=orientation_id, text=text)
        tars.chat_postMessage(channel=project_id, text=text)
        tars.chat_postMessage(channel=general_id, text=text)
    elif "post weekend ta hours" in text:
        admin = list(db.child(key_fb_tars).child("admin").get().val())
        if event_data["event"]["user"] not in admin:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You're not allowed to do this!")
            return
        fri_sun_poll = db.child(key_fb_tars).child("tapoll").child("frisun").get().val()
        poll = db.child(key_fb_tars).child("polls").child(fri_sun_poll).get().val()
        db.child(key_fb_tars).child("polls").child(fri_sun_poll).remove()
        text = "TA Hours for Friday to Sunday:\n"
        for block in poll["message"][1:-3]:
            try:
                text += block["text"]["text"].split("`")[0].strip() + " " + block["text"]["text"].split("`")[2] + "\n"
            except:
                text += block["text"]["text"] + "\n"
        tars.chat_delete(channel=sf_ta, ts=fri_sun_poll.replace("-", "."))
        tars.chat_postMessage(channel=sf_ta, text=text)
        tars.chat_postMessage(channel=orientation_id, text=text)
        tars.chat_postMessage(channel=project_id, text=text)
        tars.chat_postMessage(channel=general_id, text=text)
    elif "add publication" in text:
        message = "Visit https://sf-tars.herokuapp.com/add-publication to add the publication."
        tars.chat_postMessage(channel=event_data["event"]["channel"], text=message)
    elif "add person" in text:
        message = "Visit https://sf-tars.herokuapp.com/add-person to add yourself to the Solarillion webpage."
        tars.chat_postMessage(channel=event_data["event"]["channel"], text=message)
    elif "update app home" in text:
        users = tars.users_list().data["members"]
        users = [user["id"] for user in users]
        admin = list(db.child(key_fb_tars).child("admin").get().val())
        ta = list(db.child(key_fb_tars).child("ta").get().val())
        for user in users:
            if user in admin:
                tars.views_publish(user_id=user, view={
                    "type": "home",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "Hi 👋 I'm TARS. I help people at SF do just about everything. Here are a few things that I do:"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "plain_text",
                                    "text": "🤖 Sending notifications and information."
                                },
                                {
                                    "type": "plain_text",
                                    "text": "🤖 Booking meetings."
                                },
                                {
                                    "type": "plain_text",
                                    "text": "🤖 Scheduling and posting Sir's office hours and TA hours."
                                },
                                {
                                    "type": "plain_text",
                                    "text": "🤖 Updating JupyterHub and server SSH links."
                                },
                                {
                                    "type": "plain_text",
                                    "text": "🤖 Creating and managing polls."
                                },
                                {
                                    "type": "plain_text",
                                    "text": "🤖 Helping TAs do their job."
                                }
                            ]
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "And a whole lot more."
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*Office Hours*\nSir is sent the office hours request automatically every Saturday evening. They are posted every Sunday evening. If the server is down, use `request office hours` to request hours, `remind office hours` to remind Sir, and `post office hours` to post the hours."
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*TA Hours*\nWith the server's help, I request TAs to mark their hours for the upcoming week on Saturday. The hours for Mon-Thu are posted at 6 pm on Sunday, and the hours for Fri-Sun are posted at 6 pm on Thursday. If the server is down, use `request ta hours` to post the polls, `remind weekday ta hours` and `remind weekend ta hours` to send reminders, and `post weekday ta hours` and `post weekend ta hours` to post the hours."
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*Meetings*\nBook meetings with Sir with my help. Check the week's office hours before you book a meeting. You can also view meetings you booked and cancel them. The functions are:"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": ":point_right: `book meeting MEETING_TITLE DAY_OF_WEEK TIME DURATION`\n:arrow_right:`@PERSON_1 @PERSON_2 ...`\nExample: `book meeting Paper Review on Friday at 7pm for 15 minutes`\n`@TEAMMATE1 @TEAMMATE2`"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":exclamation: This works with simple, natural language. You can enter `minutes` or `mins`, enter a date or a day or even something like `tomorrow`. The default duration is `15 minutes`. Press `enter` or `return` after typing the meeting details to add participants, in a new line. You are added as a participant by default, so you needn't add yourself. Do not add Sir as a participant, he is also added automatically. You may choose to not add any additional participants at all."
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":point_right: `show meetings`"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":exclamation: This shows the meetings that you have booked or have been invited to this week."
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":point_right: `cancel meeting MEETING_NUMBER`\nExample: `cancel meeting 1`"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":exclamation: Use `show meetings` to list the meetings you've booked and get the `MEETING_NUMBER`. Cancel the meeting using that number. You can only cancel meetings that you booked."
                                }
                            ]
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*Polls*\nPolls can be created in all channels I've been added to by mentioning me. Use `@TARS poll \"Question\" \"Option 1\" \"Option 2\" ...` and include upto `10` options. Tap on an option to select it, and tap on it again to deselect it. The creator of the poll can close or delete the poll as well."
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*TA Orientee Tracking*\nAll TAs and Sir can add or remove orientees from the SF orientee database, track their progress and verify assignments. The functions are:"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": ":point_right: `add orientee @SLACK_ID GITHUB GROUP PYTHON_DURATION`\nExample: `add orientee @FakeOrientee fake_orientee ML 7`\nNote that PYTHON_DURATION must be `7` or `10` or `14`. Group duration is set to `14` by default while project duration is `2 months`."
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":point_right: `remove orientee @SLACK_ID`\nExample: `remove orientee @FakeOrientee`"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":point_right: `show orientee @SLACK_ID`\nExample: `show orientee @FakeOrientee`"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":point_right: `verify orientee @SLACK_ID`\nExample: `verify orientee @FakeOrientee`"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":point_right: `track all orientees` or `track all orientees sf_ta`"
                                }
                            ]
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "plain_text",
                                "text": "Well, that's it for now, but I'll be doing a lot more in the future. Use my services well. Oh, and contact the server team if you have any feature requests or need help. *flashes cue light*"
                            }
                        }
                    ]
                })
            elif user in ta:
                tars.views_publish(user_id=user, view={
                    "type": "home",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "Hi 👋 I'm TARS. I help people at SF do just about everything. Here are a few things that I do:"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "plain_text",
                                    "text": "🤖 Sending notifications and information."
                                },
                                {
                                    "type": "plain_text",
                                    "text": "🤖 Booking meetings."
                                },
                                {
                                    "type": "plain_text",
                                    "text": "🤖 Scheduling and posting Sir's office hours and TA hours."
                                },
                                {
                                    "type": "plain_text",
                                    "text": "🤖 Updating JupyterHub and server SSH links."
                                },
                                {
                                    "type": "plain_text",
                                    "text": "🤖 Creating and managing polls."
                                },
                                {
                                    "type": "plain_text",
                                    "text": "🤖 Helping TAs do their job."
                                }
                            ]
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "And a whole lot more."
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*Office Hours*\nSir is sent the office hours request automatically every Saturday evening. They are posted every Sunday evening. If the server is down, the server admins take over and request or post the office hours."
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*TA Hours*\nWith the server's help, I request TAs to mark their hours for the upcoming week on Saturday. The hours for Mon-Thu are posted at 6 pm on Sunday, and the hours for Fri-Sun are posted at 6 pm on Thursday. If the server is down, the server admins take over and request or post the hours."
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*Meetings*\nBook meetings with Sir with my help. Check the week's office hours before you book a meeting. You can also view meetings you booked and cancel them. The functions are:"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": ":point_right: `book meeting MEETING_TITLE DAY_OF_WEEK TIME DURATION`\n:arrow_right:`@PERSON_1 @PERSON_2 ...`\nExample: `book meeting Paper Review on Friday at 7pm for 15 minutes`\n`@TEAMMATE1 @TEAMMATE2`"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":exclamation: This works with simple, natural language. You can enter `minutes` or `mins`, enter a date or a day or even something like `tomorrow`. The default duration is `15 minutes`. Press `enter` or `return` after typing the meeting details to add participants, in a new line. You are added as a participant by default, so you needn't add yourself. Do not add Sir as a participant, he is also added automatically. You may choose to not add any additional participants at all."
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":point_right: `show meetings`"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":exclamation: This shows only the meetings that you have booked or have been invited to this week."
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":point_right: `cancel meeting MEETING_NUMBER`\nExample: `cancel meeting 1`"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":exclamation: Use `show meetings` to list the meetings you've booked and get the `MEETING_NUMBER`. Cancel the meeting using that number. You can only cancel meetings that you have booked."
                                }
                            ]
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*Polls*\nPolls can be created in all channels I've been added to by mentioning me. Use `@TARS poll \"Question\" \"Option 1\" \"Option 2\" ...` and include upto `10` options. Tap on an option to select it, and tap on it again to deselect it. The creator of the poll can close or delete the poll as well."
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*TA Orientee Tracking*\nAll TAs and Sir can add or remove orientees from the SF orientee database, track their progress and verify assignments. The functions are:"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": ":point_right: `add orientee @SLACK_ID GITHUB GROUP PYTHON_DURATION`\nExample: `add orientee @FakeOrientee fake_orientee ML 7`\nNote that PYTHON_DURATION must be `7` or `10` or `14`. Group duration is set to `14` by default while project duration is `2 months`."
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":point_right: `remove orientee @SLACK_ID`\nExample: `remove orientee @FakeOrientee`"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":point_right: `show orientee @SLACK_ID`\nExample: `show orientee @FakeOrientee`"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":point_right: `verify orientee @SLACK_ID`\nExample: `verify orientee @FakeOrientee`"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":point_right: `track all orientees` or `track all orientees sf_ta`"
                                }
                            ]
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "plain_text",
                                "text": "Well, that's it for now, but I'll be doing a lot more in the future. Use my services well. Oh, and contact the server team if you have any feature requests or need help. *flashes cue light*"
                            }
                        }
                    ]
                })
            else:
                tars.views_publish(user_id=user, view={
                    "type": "home",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "Hi 👋 I'm TARS. I help people at SF do just about everything. Here are a few things that I do:"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "plain_text",
                                    "text": "🤖 Sending notifications and information."
                                },
                                {
                                    "type": "plain_text",
                                    "text": "🤖 Scheduling and posting Sir's office hours and TA hours."
                                },
                                {
                                    "type": "plain_text",
                                    "text": "🤖 Updating JupyterHub and server SSH links."
                                },
                                {
                                    "type": "plain_text",
                                    "text": "🤖 Booking meetings."
                                },
                                {
                                    "type": "plain_text",
                                    "text": "🤖 Creating and managing polls."
                                },
                                {
                                    "type": "plain_text",
                                    "text": "🤖 Helping TAs do their job."
                                }
                            ]
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "And a whole lot more."
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*Office Hours*\nSir is sent the office hours request automatically every Saturday evening. They are posted every Sunday evening. If the server is down, the server admins take over and request or post the office hours."
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*TA Hours*\nWith the server's help, I request TAs to mark their hours for the upcoming week on Saturday. The hours for Mon-Thu are posted at 6 pm on Sunday, and the hours for Fri-Sun are posted at 6 pm on Thursday. If the server is down, the server admins take over and request or post the hours."
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*Meetings*\nBook meetings with Sir with my help. Check the week's office hours before you book a meeting. You can also view meetings you booked and cancel them. The functions are:"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": ":point_right: `book meeting MEETING_TITLE DAY_OF_WEEK TIME DURATION`\n:arrow_right:`@PERSON_1 @PERSON_2 ...`\nExample: `book meeting Paper Review on Friday at 7pm for 15 minutes`\n`@TEAMMATE1 @TEAMMATE2`"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":exclamation: This works with simple, natural language. You can enter `minutes` or `mins`, enter a date or a day or even something like `tomorrow`. The default duration is `15 minutes`. Press `enter` or `return` after typing the meeting details to add participants, in a new line. You are added as a participant by default, so you needn't add yourself. Do not add Sir as a participant, he is also added automatically. You may choose to not add any additional participants at all."
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":point_right: `show meetings`"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":exclamation: This shows only the meetings that you have booked or have been invited to this week."
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":point_right: `cancel meeting MEETING_NUMBER`\nExample: `cancel meeting 1`"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": ":exclamation: Use `show meetings` to list the meetings you've booked and get the `MEETING_NUMBER`. Cancel the meeting using that number. You can only cancel meetings that you booked."
                                }
                            ]
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*Polls*\nPolls can be created in all channels I've been added to by mentioning me. Use `@TARS poll \"Question\" \"Option 1\" \"Option 2\" ...` and include upto `10` options. Tap on an option to select it, and tap on it again to deselect it. The creator of the poll can close or delete the poll as well."
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "plain_text",
                                "text": "Well, that's it for now, but I'll be doing a lot more in the future. Use my services well. Oh, and contact the server team if you have any feature requests or need help. *flashes cue light*­"
                            }
                        }
                    ]
                })
    elif any([a in text.split() for a in ["hi", "hello"]]):
        tars.chat_postMessage(channel=event_data["event"]["channel"], text="TARS says 👋 back. *flashes cue light*­")

def reformat_time(ts):
    t = time.fromisoformat(ts[11:19])
    t = datetime.combine(date.today(), t) + timedelta(hours=5, minutes=21, seconds=10)
    return t.strftime("%I:%M %p")

def reformat_meeting_date(ts):
    d = date.fromisoformat(ts[:10])
    h = int(ts.split(":")[0][-2:]) + 5
    if h >= 24:
        d = d + timedelta(days=1)
    return d.strftime("%d-%m-%Y")

def reformat_meeting_time(ts):
    t = time.fromisoformat(ts[11:19])
    t = datetime.combine(date.today(), t) + timedelta(hours=5, minutes=30)
    return t.strftime("%I:%M %p")

@slack_events_adapter.on("team_join")
def team_join(event_data):
    thread = threading.Thread(target=team_join_event_handler, args=(event_data,))
    thread.start()
    return "OK", 200

def team_join_event_handler(event_data):
    user = event_data["event"]["user"]["id"]
    im_request = tars.im_open(user=user)
    chat = im_request.data["channel"]["id"]
    tars.chat_postMessage(channel=chat, text="Hello there!", blocks=[
        {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": "Hello there! I'm TARS, and I help people at Solarillion do almost every task on Slack. You can visit the Home tab at any time to see what you need to tell me to get things done. I hope you enjoy your journey here. See you soon. *flashes cue light*­"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Oh, and one more thing. Carefully read the README file in the PythonBasics repository on GitHub (https://github.com/solarillion/PythonBasics) before you get started with your assignments. The Webhook URL is https://sf-hyouka.herokuapp.com/python and the Secret is `" + github_secret + "` (you'll need these later). Please do not share this anywhere else or with anyone else. Contact a TA if you have any other doubts. Bye for now!"
            }
        }
    ])
    tars.chat_postMessage(channel=orientation_id, text="The Python assignments are available at https://github.com/solarillion/PythonBasics along with instructions. Create a GitHub account if you don't have one and follow the instructions given to do your assignments. Don't hesitate to contact a TA if you have any doubts!")

@slack_events_adapter.on("app_mention")
def app_mention(event_data):
    thread = threading.Thread(target=app_mention_event_handler, args=(event_data,))
    thread.start()
    return "OK", 200
    
def app_mention_event_handler(event_data):
    text = event_data["event"]["text"]
    if "poll" in text.lower():
        try:
            text = text.replace(u"\u201c", u"\u0022").replace(u"\u201d", u"\u0022")
            text = shlex.split(text)[2:]
            question = text[0]
            options = text[1:]
            emoji = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "keycap_ten"]
            if len(options) > 10:
                raise Exception("Too many options!")
            question_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*" + question + "*"
                }
            }
            options_blocks = []
            for i in range(len(options)):
                options_blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":" + emoji[i] + ": " + options[i]
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": ":" + emoji[i] + ":"
                        },
                        "value": emoji[i] + "_poll"
                    }
                })
            options_blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": ":white_check_mark: End Poll"
                        },
                        "value": "end_poll"
                    }
                ]
            })
            options_blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": ":x: Delete Poll"
                        },
                        "value": "delete_poll"
                    }
                ]
            })
            try:
                options_blocks.append({
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "Created by <@" + event_data["event"]["user"] + "> using TARS."
                        }
                    ]
                })
            except:
                options_blocks.append({
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "Created using TARS."
                        }
                    ]
                })
            poll = tars.chat_postMessage(channel=event_data["event"]["channel"], text=question + " Poll", blocks=[question_block] + options_blocks)
            db.child(key_fb_tars).child("polls").child(poll.data["ts"].replace(".", "-")).update({"user": event_data["event"]["user"], "question": question, "message": [question_block] + options_blocks})
            if question == "Mon-Thu TA Hours":
                db.child(key_fb_tars).child("tapoll").update({"monthu": poll.data["ts"].replace(".", "-")})
            elif question == "Fri-Sun TA Hours":
                db.child(key_fb_tars).child("tapoll").update({"frisun": poll.data["ts"].replace(".", "-")})
        except Exception as e:
            print(e)
            tars.chat_postEphemeral(channel=event_data["event"]["channel"], user=event_data["event"]["user"], text="Syntax for polls is `@TARS poll \"Question\" \"Option 1\" \"Option 2\" ...` with a maximum of `10` options.")

@app.route("/interact", methods=["POST"])
def interact():
    payload = json.loads(request.form.get("payload"))
    thread = threading.Thread(target=interact_handler, args=(payload,))
    thread.start()
    return "OK", 200

def interact_handler(payload):
    user = payload["user"]["id"]
    channel = payload["container"]["channel_id"]
    ts = payload["message"]["ts"]
    value = payload["actions"][0]["value"]
    question = db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("question").get().val()
    if value == "delete_poll":
        if db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("user").get().val() == user:
            tars.chat_update(channel=channel, ts=ts, text="Poll " + question + " deleted!", blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Poll " + question + " deleted!"
                    }
                }
            ])
            db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).remove()
        else:
            tars.chat_postEphemeral(channel=channel, user=user, text="You can only delete polls that you create.")
    elif value == "end_poll":
        if db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("user").get().val() == user:
            tars.chat_update(channel=channel, ts=ts, text="Poll " + question + " closed!", blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Poll " + question + " closed!"
                    }
                }
            ])
            poll = db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).get().val()
            db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).remove()
            tars.chat_postMessage(channel=channel, text="*Poll Results*")
            for block in poll["message"][1:-3]:
                text = block["text"]["text"]
                tars.chat_postMessage(channel=channel, text=text)
        else:
            tars.chat_postEphemeral(channel=channel, user=user, text="You can only close polls that you create.")
    elif "_poll" in value:
        emoji = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "keycap_ten"]
        value = value.split("_")[0]
        index = emoji.index(value) + 1
        poll = db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).get().val()
        votes = db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("votes").child(str(index)).get().val()
        if votes is None:
            db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("votes").child(str(index)).update({0: user})
            current = db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("message").child(str(index)).child("text").child("text").get().val()
            db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("message").child(str(index)).child("text").update({"text": current.strip() + " `1` ~ <@" + user + ">"})
        else:
            current = db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("message").child(str(index)).child("text").child("text").get().val()
            if user not in current:
                i = len(votes)
                db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("votes").child(str(index)).update({i: user})
                db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("message").child(str(index)).child("text").update({"text": current.split("`")[0] + "`" + str(i + 1) + "` ~ <@" + user + ">" + current.split("~")[1]})
            else:
                for i in votes:
                    if i == user:
                        votes.remove(i)
                db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("votes").child(str(index)).remove()
                j = 0
                for i in votes:
                    db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("votes").child(str(index)).update({j: i})
                    j += 1
                current = db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("message").child(str(index)).child("text").child("text").get().val()
                if j == 0:
                    db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("message").child(str(index)).child("text").update({"text": current.split("`")[0]})
                else:
                    db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("message").child(str(index)).child("text").update({"text": current.split("`")[0] + "`" + str(j) + "` ~ " + current.split("~")[1].replace("<@" + user + ">", "").strip()})
        blocks = dict(db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).get().val())["message"]
        tars.chat_update(channel=channel, ts=ts, blocks=blocks)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        data1 = {}
        data1["status"] = "Enter credentials."
        return render_template("login.html", data=data1)
    if request.method=="POST":
        username_form = request.form.get("username")
        password_form = request.form.get("password").encode()
        if username_form == username and bcrypt.checkpw(password_form, password):
            user = User()
            user.id = username
            flask_login.login_user(user)
            data1 = {}
            data1["status"] = "Enter the details and submit."
            return redirect(request.args.get("next") or url_for("index"))
        else:
            data1 = {}
            data1["status"] = "Incorrect credentials."
            return render_template("login.html", data=data1)

def git_clone(full_local_path: str):
    try:
        shutil.rmtree(full_local_path)
    except:
        pass
    remote = f"https://{github_username}:{github_password}@github.com/solarillion/solarillion.github.io.git"
    Repo.clone_from(remote, full_local_path)
    
def git_push(full_local_path, branch_name, commit_message, pr_title, pr_body):
    repo = Repo(full_local_path)
    repo.config_writer().set_value("user", "name", github_username).release()
    repo.config_writer().set_value("user", "email", github_email).release()
    
    repo.git.checkout("-b", branch_name)

    repo.git.add('.')
    repo.index.commit(commit_message)
    origin = repo.remote(name="origin")
    origin.push(branch_name)

    shutil.rmtree("solarillion.github.io")
    g = Github(github_password)
    repo = g.get_repo("solarillion/solarillion.github.io")
    _ = repo.create_pull(title=pr_title, body=pr_body, head=branch_name, base="master")

@app.route("/add-publication", methods=["GET", "POST"])
@flask_login.login_required
def add_publication():
    try:
        full_local_path = "solarillion.github.io"
        if request.method == "GET":
            data1 = {}
            data1["status"] = "Enter the details and submit."
            git_clone(full_local_path)
            with open("solarillion.github.io/_data/people.yml", "r") as file:
                people_data = load(file, Loader=yaml.FullLoader)
            data1["people"] = people_data
            return render_template("add-publication.html", data=data1)

        with open("solarillion.github.io/_data/people.yml", "r") as file:
            people_data = load(file, Loader=yaml.FullLoader)
        record = {}
        record["title"] = str(request.form["pname"])
        record["conference"] = str(request.form["cname"])
        record["year"] = str(request.form["cyear"])
        record["status"] = request.form["status"]
        record["team"] = request.form["team"]
        authors = request.form.getlist("authors")
        authors_full_name = []
        for i in authors:
            authors_full_name.append(people_data[i]["name"])
        record["authors"] = authors_full_name
        outr_d = {}
        pkey = ""
        title_upper = record["title"].upper()
        for i in title_upper.split(" "):
            pkey += i[0]
        outr_d[pkey] = record
        
        with open("solarillion.github.io/_data/publications.yml", "a") as file:
                dump(outr_d, file, width=1000)
        
        branch_name = 'add-publication-' + pkey
        commit_message = "publications.yml: added publication"
        pr_title = "Added new publication"
        pr_body = "Added a new publication: \"" + record["title"] + "\"."

        git_push(full_local_path, branch_name, commit_message, pr_title, pr_body)
        
        data1 = {}
        data1["status"] = "The publication will be added to the website."
        return render_template("login.html",data=data1) 
    except Exception as e:
        message = "An error occurred while adding publication: " + str(request.form['pname'])
        message += "\nException:\n" + str(e)
        tars.chat_postMessage(channel=tars_admin, text=message)


@app.route("/add-person", methods=['GET', 'POST'])
@flask_login.login_required
def addperson():
    if request.method == 'GET':
        return render_template('add-person.html')
 
    try:
        data = request.form
        img_file = request.files['file']
        full_local_path = "solarillion.github.io"
        git_clone(full_local_path)

        person = data['name'].replace(" ","") + ":\n"
        person += '  group: ra\n'
        person += '  avatar: /assets/images/headshots/' + data['name'].replace(" ","") +\
            '.' + img_file.filename.split('.')[-1].lower() + "\n"
        person += '  page: /people/' + data['name'].replace(" ","") + "\n"
        for key in data.keys():
            if key == 'bio':
                roles = data.getlist(key)
                temp_str = ', '.join(roles)
                person += '  bio: ' + temp_str + '\n'
            elif key == 'about':
                person += '  about:\n    \"' + data.get(key) + '\"\n\n'
            else:
                value = data.get(key)
                if len(value) > 0:
                    person += '  ' + key + ': ' + value + '\n'
        
        with open("solarillion.github.io/_data/people.yml", 'at') as file:
            file.write(person)

        with open('templates/person_template.html', 'rt') as file:
            html = file.read()
            name = data['name']
            html = html.replace('{{name}}', name)
            html = html.replace('{{name_trim}}', name.replace(' ',''))
            html = html.replace('{{first_name}}', name.split(' ')[0])

            with open('solarillion.github.io/_pages/people/' + name.replace(' ','') + '.html', 'wt') as fout:
                fout.write(html)

        img_save_path = 'solarillion.github.io/assets/images/headshots/'
        
        filename = data['name'].replace(' ', '') + '.'
        filename += img_file.filename.split('.')[-1].lower()
        img_file.save(img_save_path + secure_filename(filename))

        branch_name = 'add-person-' + data['name'].split(' ')[0].lower()
        commit_message = "added new research assistant"
        pr_body = 'Added new Research Assistant: ' + data['name']
        pr_title = 'Added new Research Assistant'

        git_push(full_local_path, branch_name, commit_message, pr_title, pr_body)

    except Exception as e:
        message = "An error occurred while adding person: " + str(data['name'])
        message += "\nException:\n" + str(e)
        tars.chat_postMessage(channel=tars_admin, text=message)

    return redirect(url_for('logout'))    
    


@app.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(threaded=True)
