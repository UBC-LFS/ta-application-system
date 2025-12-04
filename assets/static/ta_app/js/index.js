$(document).ready(function() {

  // Make a navigation header active
  const roles = window.location.pathname.split('/');

  if (roles[2] === 'administrators') {
    $('#nav-administrator').addClass('active');

  } else if (roles[2] === 'instructors') {
    $('#nav-instructor').addClass('active');

  } else if (roles[2] === 'students') {
    $('#nav-student').addClass('active');

  } else if (roles[2] === 'observers') {
    $('#nav-observer').addClass('active');

  } else if (roles[2] === 'users') {

    const parameters = window.location.href.split('?');
    if ( parameters[1].includes('administrators') ) {
      $('#nav-administrator').addClass('active');

    } else if ( parameters[1].includes('instructors') ) {
      $('#nav-instructor').addClass('active');

    } else if ( parameters[1].includes('students') ) {
      $('#nav-student').addClass('active');

    } else if ( parameters[1].includes('observers') ) {
      $('#nav-observer').addClass('active');
    }
  }

  // Remove admin docs data
  if ( sessionStorage.getItem('admin-docs') ) {
    const data = JSON.parse( sessionStorage.getItem('admin-docs') );
    $("#admin-docs-form-message").append(data.message);
    sessionStorage.removeItem('admin-docs');
  }

  // Summernote settings
  $('.summernote').summernote({
    height: 150,
    toolbar: []
  });

  // Remove external style
  $('.WebKit-mso-list-quirks-style').remove();

});


/* Helper functions */

// Download data to a CSV file
function downloadCSV(data, filename) {
  let el = document.createElement('a');
  const blob = new Blob([data], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  el.href = url;
  el.setAttribute('download', filename);
  el.click();
}

// Download data to a text file
function downloadText(data, filename) {
  let el = document.createElement('a');
  const blob = new Blob([data], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  el.href = url;
  el.setAttribute('download', filename);
  el.click();
}

// Download data to a markdown file
function downloadText(data, filename) {
  let el = document.createElement('a');
  const blob = new Blob([data], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  el.href = url;
  el.setAttribute('download', filename);
  el.click();
}

// Download data to an Excel file
function downloadExcel(data, filename) {
  const worksheet = XLSX.utils.json_to_sheet(data);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Sheet1');
  XLSX.writeFile(workbook, filename, { compression: true });
}


// Get today's date format
function getToday() {
  var d = new Date(),
      month = '' + (d.getMonth() + 1),
      day = '' + d.getDate(),
      year = d.getFullYear();

  if (month.length < 2) month = '0' + month;
  if (day.length < 2) day = '0' + day;

  return [year, month, day].join('-');
}

function replaceNewLine(str) {
  return str.trim().replace(/\n/g, ' ');
}
