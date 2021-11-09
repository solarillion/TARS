// Google Apps Script for handling Meetings
// Replace the URLs as required

// Function to clear meetings from the database
// Trigger: Time-based, Weekly, Sunday 8-9 pm
function clearFunction() {
  var meetingsUrl = MEETINGS_URL;
  var bookingsUrl = BOOKINGS_URL;
  var cancelsUrl = CANCELS_URL;
  var options = {
    'method' : 'delete'
  };
  UrlFetchApp.fetch(meetingsUrl, options);
  UrlFetchApp.fetch(bookingsUrl, options);
  UrlFetchApp.fetch(cancelsUrl, options);
}

// Function to add meetings from the database to the calendar
// Trigger: Time-based, Every 1 minute
function addEvent() {
  var bookingsUrl = BOOKINGS_URL;
  var result = UrlFetchApp.fetch(bookingsUrl);
  var data = JSON.parse(result.getContentText());
  var deletion = {
    'method' : 'delete'
  };
  for(var l in data) {
    itemUrl = BOOKINGS_URL_WITHOUT_JSON + l + "/.json";
    meetingUrl = MEETINGS_URL_WITHOUT_JSON + l + "/.json";
    var event = CalendarApp.createEventFromDescription(data[l].meeting);
    var guestList = []  
    for(var e = 0; e < data[l].people.length; e++) {
      guestList.push({"email": data[l].people[e]})
    }
    var updatedEvent = {
      "start": {
        "dateTime": event.getStartTime().toISOString(),
        "timeZone": CalendarApp.getTimeZone()
      },
      "end": {
        "dateTime": event.getEndTime().toISOString(),
        "timeZone": CalendarApp.getTimeZone()

      },
      "attendees" : guestList,
      "description" : event.getDescription(),
      "summary": event.getTitle(),
      "conferenceData" : {
        "createRequest": {
          "conferenceSolutionKey": {
              "type": "hangoutsMeet"
          },
          "requestId": event.getId()
        }
      }
    };
    event = Calendar.Events.update(updatedEvent, 'primary', event.getId().split("@")[0], {conferenceDataVersion: 1});

    UrlFetchApp.fetch(itemUrl, deletion);
    payload = {
      id:event.getId(),
      start:event.getStartTime(),
      end:event.getEndTime(),
      desc:event.getTitle()
      people:data[l].people_slack
    };
    var options = {
    'method' : 'patch',
    'contentType': 'application/json',
    'payload' : JSON.stringify(payload)
    };
    UrlFetchApp.fetch(meetingUrl, options);
  }
}

// Function to remove meetings from the calendar
// Trigger: Time-based, Every 1 minute
function cancelEvent() {
  var cancelsUrl = CANCELS_URL;
  var result = UrlFetchApp.fetch(cancelsUrl)
  var data = JSON.parse(result.getContentText());
  var deletion = {
    'method' : 'delete'
  };
  for(var l in data) {
    itemUrl = CANCELS_URL_WITHOUT_JSON + l + "/.json";
    meetingUrl = MEETINGS_URL_WITHOUT_JSON + l + "/.json";
    var meeting = UrlFetchApp.fetch(meetingUrl);
    var m = JSON.parse(meeting.getContentText());
    var id = m.id;
    var event = CalendarApp.getEventById(id);
    event.deleteEvent();
    UrlFetchApp.fetch(itemUrl, deletion);
    UrlFetchApp.fetch(meetingUrl, deletion);
  }
}
