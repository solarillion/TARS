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
    rows.push([i, data[i].name, data[i].github, data[i].group, data[i].progress, data[i].join, data[i].py_fin, data[i].g_fin, data[i].p_fin]);
  }
  var sheet = SpreadsheetApp.getActive().getSheets()[0];
  dataRange = sheet.getRange(2, 1, rows.length, 9);
  dataRange.setValues(rows);
}
