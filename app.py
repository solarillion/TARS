# Authors: Nanda H Krishna (https://github.com/nandahkrishna)

import os
from datetime import *
from dateutil.relativedelta import *
from dateutil.rrule import *
import json
from urllib.parse import parse_qs
import requests
import threading
from flask import Flask, jsonify, redirect, request
import slack
from slackeventsapi import SlackEventAdapter
import pyrebase

app = Flask(__name__)
app.debug = True

tars_token = os.environ.get("TARS_TOKEN")
tars_user_token = os.environ.get("TARS_USER_TOKEN")
tars_admin = os.environ.get("TARS_ADMIN")
tars_secret = os.environ.get("TARS_SECRET")
tars_bot_id = os.environ.get("TARS_BOT_ID")
general_id = os.environ.get("GENERAL_ID")
orientation_id = os.environ.get("ORIENTATION_ID")
project_id = os.environ.get("PROJECT_ID")
sf_research = os.environ.get("SF_RESEARCH")
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
        tars.chat_postMessage(channel=vineethv_im_channel, text="Sir, please fill your office hours in this form: https://forms.gle/eMoayTXg5KJCata68")
    elif "remind office hours" in text:
        tars.chat_postMessage(channel=vineethv_im_channel, text="Sir, if you haven't filled your office hours yet, please do so by 9 pm tonight. Here's the link to the form: " + office_hours_form)
    elif "post office hours" in text:
        data = db.child(key_fb_tars).child("officehours").get().val()
        message = "Sir's office hours for the week:\n"
        for item in data[1:]:
            item["start"] = reformat_time(item["start"])
            item["end"] = reformat_time(item["end"])
            message += item["days"] + ": " + item["start"] + " - " + item["end"] + "\n"    
        tars.chat_postMessage(channel=general_id, text=message)
    elif "add orientee" in text:
        ta = list(db.child(key_fb_tars).child("ta").get().val())
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
        if "O" in group:
            group = "IoT"
        db.child(key_fb_tars).child("orientee").child(slack_id).update({ "name": name, "join": join, "github": github, "group": group, "progress": "py1", "py_fin": "None", "g_fin": "None", "p_fin": "None"})
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
        data = db.child(key_fb_tars).child("orientee").child(slack_id).get().val()
        message = "Progress of " + data["name"] + ":\nJoined: " + data["join"] + "\nGroup: " + data["group"] + "\nStatus: " + data["progress"]
        if data["py_fin"] != "None":
            message += "\nPython end: " + data["py_fin"]
        if data["g_fin"] != "None":
            message += "\nGroup end: " + data["g_fin"]
        if data["p_fin"] != "None":
            message += "\nProject end: " + data["p_fin"] + "\nAfter the project review, don't forget to remove orientee."
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
        new_status = {"py2": "py3", "py3": data["group"].lower() + "1", "ml1": "ml2", "ml2": "ml3", "ml3": "mlp", "iot1": "iot2", "iot2": "iot3", "iot3": "iotp", "mg1": "mg2", "mg2": "mg3", "mg3": "mgp"}
        if status == "py1":
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="Verification for py1 will be done through Hyouka.")
        elif status == "py2" or status == "py3":
            hyouka_status = hyouka_db.child(key_fb_hyouka).child(github).get().val()["progress"]
            if hyouka_status == status + "v":
                db.child(key_fb_tars).child("orientee").child(slack_id).update({"progress": new_status[status]})
                hyouka_db.child(key_fb_hyouka).child(github).update({"progress": new_status[status]})
                tars.chat_postMessage(channel=event_data["event"]["channel"], text="Verified " + status + "!")
                orientee = tars.im_open(user=slack_id).data["channel"]["id"]
                tars.chat_postMessage(channel=orientee, text="Verified " + status + "! Move on to " + new_status[status] + " now.")
                if status == "py3":
                    db.child(key_fb_tars).child("orientee").child(slack_id).update({"py_fin": str(date.today())})
                    group = db.child(key_fb_tars).child("orientee").child(slack_id).child("group").get().val()
                    tars.chat_postMessage(channel=event_data["event"]["channel"], text="On to the " + group + " assignments now.")
            else:
                tars.chat_postMessage(channel=event_data["event"]["channel"], text="Not yet evaluated on Hyouka!")
        elif "p" != status[-1]:
            db.child(key_fb_tars).child("orientee").child(slack_id).update({"progress": new_status[status]})
            hyouka_db.child(key_fb_hyouka).child(github).update({"progress": new_status[status]})
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="Verified " + status + "!")
            orientee = tars.im_open(user=slack_id).data["channel"]["id"]
            tars.chat_postMessage(channel=orientee, text="Verified " + status + "! Move on to " + new_status[status] + " now.")
            if "p" in new_status[status]:
                db.child(key_fb_tars).child("orientee").child(slack_id).update({"g_fin":str( date.today())})
                group = db.child(key_fb_tars).child("orientee").child(slack_id).child("group").get().val()
                tars_user.groups_kick(channel=orientation_id, user=slack_id)
                tars_user.groups_invite(channel=project_id, user=slack_id)
                tars.chat_postMessage(channel=event_data["event"]["channel"], text="On to the " + group + " project now. Next verification only after Sir's reviews.")
        else:
            db.child(key_fb_tars).child("orientee").child(slack_id).update({"progress": "done"})
            db.child(key_fb_tars).child("orientee").child(slack_id).update({"p_fin": str(date.today())})
            hyouka_db.child(key_fb_hyouka).child(github).update({"progress": "done"})
            tars_user.groups_kick(channel=project_id, user=slack_id)
            tars_user.groups_invite(channel=sf_research, user=slack_id)
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="Verified! Project and reviews complete, added orientee to #sf_research.")
            orientee = tars.im_open(user=slack_id).data["channel"]["id"]
            tars.chat_postMessage(channel=orientee, text="You have completed your project. Great work!")
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
        people = [slack_id]
        if len(lines) == 2:
            add =  lines[1].replace("@", "").replace("<", "").replace(">", "").upper().split()
            add = list(map(lambda x: tars.users_info(user=x).data["user"]["profile"]["email"], add))
            people = people + add
        db.child(key_fb_tars).child("bookings").child(id).set({"meeting": meeting, "people": people})
        tars.chat_postMessage(channel=event_data["event"]["channel"], text="The meeting has been booked!")
    elif "show meeting" in text:
        slack_id = event_data["event"]["user"]
        meetings = db.child(key_fb_tars).child("meetings").get().val()
        if meetings is not None:
            for i in list(meetings):
                if slack_id in i:
                    item = db.child(key_fb_tars).child("meetings").child(i).get().val()
                    text = "`" + i.split("_")[1] + "`: " + item["desc"] + ", " + reformat_meeting_date(item["start"]) + " " + reformat_meeting_time(item["start"]) + " - " + reformat_meeting_time(item["end"])
                    tars.chat_postMessage(channel=event_data["event"]["channel"], text=text)
        else:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You haven't booked any meetings!")
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
        pass
    elif "remind weekday ta hours" in text:
        pass
    elif "remind weekend ta hours" in text:
        pass
    elif "post weekday ta hours" in text:
        pass
    elif "post weekend ta hours" in text:
        pass

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

@slack_events_adapter.on("app_home_opened")
def app_home_opened(event_data):
    thread = threading.Thread(target=app_home_opened_event_handler, args=(event_data,))
    thread.start()
    return "OK", 200
    
def app_home_opened_event_handler(event_data):
    user = event_data["event"]["user"]
    ta = list(db.child(key_fb_tars).child("ta").get().val())
    if user in ta:
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
                                "text": ":exclamation: This shows only the meetings that you have booked this week."
                            },
                            {
                                "type": "mrkdwn",
                                "text": ":point_right: `cancel meeting MEETING_NUMBER`\nExample: `cancel meeting 1`"
                            },
                            {
                                "type": "mrkdwn",
                                "text": ":exclamation: Use `show meetings` to list the meetings you've booked and get the `MEETING_NUMBER`. Cancel the meeting using that number."
                            }
                        ]
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
                                "text": ":point_right: `add orientee @SLACK_ID GITHUB GROUP`\nExample: `add orientee @FakeOrientee fake_orientee ML`"
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
                            "type": "plain_text",
                            "text": "Well, that's it for now, but I'll be doing a lot more in the future. Use my services well. Oh, and contact the server team if you have any feature requests or need help. *flashes cue light*­"
                        }
                    }
                ]
        })

@slack_events_adapter.on("app_mention")
def app_mention(event_data):
    thread = threading.Thread(target=app_mention_event_handler, args=(event_data,))
    thread.start()
    return "OK", 200
    
def app_mention_event_handler(event_data):
    text = event_data["event"]["text"]
    if "poll" in text.lower():
        try:
            text = text.split()[2:]
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
            options_blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Created by <@" + event_data["event"]["user"] + "> using TARS."
                    }
                ]
            })
            poll = tars.chat_postMessage(channel=event_data["event"]["channel"], text=question + " Poll", blocks=[question_block] + options_blocks)
            db.child(key_fb_tars).child("polls").child(poll.data["ts"].replace(".", "-")).update({"user": event_data["event"]["user"], "question": question, "message": [question_block] + options_blocks, "votes": {str(i): ["-"] for i in options_blocks[:-2]}})
        except Exception as e:
            print(e)
            tars.chat_postEphemeral(channel=event_data["event"]["channel"], user=event_data["event"]["user"], text="Syntax for polls is `@TARS poll question option1 option2 ...` with a maximum of `10` options.")

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
    if value == "delete_poll":
        if db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("user").get().val() == user:
            tars.chat_deleete(channel=channel, ts=ts)
            tars.chat_postMessage(channel=channel, text="Poll deleted!")
            db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).remove()
        else:
            tars.chat_postEphemeral(channel=channel, user=user, text="You can only close polls that you create.")
    elif value == "end_poll":
        if db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("user").get().val() == user:
            tars.chat_delete(channel=channel, ts=ts)
            tars.chat_postMessage(channel=channel, text="Poll closed!")
            poll = db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).get().val()
            db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).remove()
            text = "*Poll Results*\n"
            for block in poll["message"][1:-2]:
                text = block["accessory"]["text"]["text"] + "\n"
            tars.chat_postMessage(channel=channel, text=text)
        else:
            tars.chat_postEphemeral(channel=channel, user=user, text="You can only delete polls that you create.")
    elif "_poll" in value:
        emoji = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "keycap_ten"]
        value = value.split("_")[0]
        index = emoji.index(value) + 1
        poll = db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).get().val()
        votes = poll["votes"][index]
        
if __name__ == "__main__":
    app.run(threaded=True)
