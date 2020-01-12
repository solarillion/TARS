// Google Apps Script for Orientee Tracking
// Container: Orientee Progress Tracker Google Sheet
// Replace FIREBASE_URL with the TARS Firebase URL

// Function to update sheet from database
// Trigger: Time-based, Every 10 minutes
function updateProgress() {
  var spreadsheet = SpreadsheetApp.getActive();
  var range = spreadsheet.getSheets()[0].getLastRow();
  spreadsheet.getSheets()[0].deleteRows(2, range - 1);
  var firebaseUrl = FIREBASE_URL;
  var result = UrlFetchApp.fetch(firebaseUrl);
  var data = JSON.parse(result.getContentText());
  var rows = [];
  for(var i in data) {
    rows.push([data[i].name, data[i].group, data[i].progress, data[i].join, data[i].pyd, data[i].py1_d, data[i].py1_fin, data[i].py2_d, data[i].py2_fin, data[i].py3_d, data[i].py3_fin, data[i].gd, data[i].g1_d, data[i].g1_fin, data[i].g2_d, data[i].g2_fin, data[i].g3_d, data[i].g3_fin, data[i].pd, data[i].p_d, data[i].p_fin]);
  }
  var sheet = SpreadsheetApp.getActive().getSheets()[0];
  dataRange = sheet.getRange(2, 1, rows.length, 21);
  dataRange.setValues(rows);
}
