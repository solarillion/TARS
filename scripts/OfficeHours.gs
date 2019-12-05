// Google Apps Script for handling Office Hours
// Container: Office Hours Google Form
// Replace SPREADSHEET_ID and FIREBASE_URL with the Office Hours (Responses) sheet ID and the TARS Firebase URL respectively

// Function to clear form, sheet and database
// Trigger: Time-based, Weekly, Saturday 6-7 pm
function clearFunction() {
  var form = FormApp.getActiveForm();
  form.deleteAllResponses();
  var spreadsheet = SpreadsheetApp.openById(SPREADSHEET_ID);
  spreadsheet.deleteRows(2, 10);
  var firebaseUrl = FIREBASE_URL;
  var options = {
    'method' : 'delete'
  };
  UrlFetchApp.fetch(firebaseUrl, options);
}

// Function to clear and overwrite database with new set of office hours
// Trigger: Form-based, On submit
function writeDataToFirebase() {
  var firebaseUrl = FIREBASE_URL;
  var options = {
    'method' : 'delete'
  };
  UrlFetchApp.fetch(firebaseUrl, options);
  var spreadsheet = SpreadsheetApp.openById(SPREADSHEET_ID);
  var sheet = spreadsheet.getSheets()[0];
  var data = sheet.getDataRange().getValues();
  var dataToImport = {};
  for(var i = 1; i < data.length; i++) {
    dataToImport[i] = {
      days:data[i][1],
      start:data[i][2],
      end:data[i][3]
    };
  }
  var options = {
    'method' : 'patch',
    'contentType': 'application/json',
    'payload' : JSON.stringify(dataToImport)
  };
  UrlFetchApp.fetch(firebaseUrl, options);
}
