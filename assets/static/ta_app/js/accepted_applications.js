$(document).ready(function() {

  // Update admin docs
  $('form .btn-submit').on('click', function(e) {
    e.preventDefault();

    const appId = $(this).data('app-id');
    const formData = $('#admin-docs-form-' + appId).serializeArray();
    $.ajax({
      method: 'POST',
      url: $(this).data('url'),
      data: formDataToJson(JSON.stringify(formData)),
      dataType: 'json',
      success: function(res) {
        let message = '<div class="alert alert-STATUS alert-dismissible fade show" role="alert">' +
                        res.message +
                        '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>' +
                      '</div>';

        if (res.status === 'success') message = message.replace('STATUS', 'success');
        else message = message.replace('STATUS', 'danger');

        sessionStorage.setItem( 'admin-docs', JSON.stringify({ 'status': res.satus, 'message': message }) );
        location.reload();
      },
      error: function(err) {
        const message = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' +
                          'Error: ' + err.statusText + ' (' + err.status + '). ' + err.responseJSON.message +
                          '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>' +
                        '</div>';
        $('#admin-docs-form-' + appId + '-error').html(message);
     }
   });
 });

 // Make a table default
 $('#btn-default-table').on('click', function() {
   sessionStorage.removeItem('sortable-table');
   location.reload();
 });

 // Check if sortable table is enabled or not
 if (sessionStorage.getItem('sortable-table')) {
   const data = JSON.parse(sessionStorage.getItem('sortable-table'));
   sortColumn(data.col, data.type, 'sessionStorage');
 }

 // Export accepted applications as a csv
 $('#export-accepted-apps-csv').on('click', function() {
   const table = $("#accepted-apps-table")[0];
   const rows = table.rows;
   const header = getHeader(rows);
   let tableData = header.join(',') + '\n';

   for (let i = 1; i < rows.length; i++) {
     let rowData = '';
     for (let j = 0; j < rows[i].children.length-1; j++) {
       let col = rows[i].children[j];
       if (col.children.length > 1) {
         let str = '"';
         if (col.children[1].innerText.length === 0) {
           str += replaceNewLine(col.children[0].innerText).replace(/\"/g, "\"\"") + '",';
          } else {
            str += replaceNewLine(col.children[0].innerText) + ' ' + replaceNewLine(col.children[1].innerText) + '",';
          }
          rowData += str;
        } else {
          rowData += '"' + replaceNewLine(col.innerText) + '",';
        }
      }
      tableData += rowData.substring(0, rowData.length - 1) + '\n';
    }

    const filename = 'TA App - Accepted Applications ' + getToday() + '.csv';
    downloadCSV(tableData, filename);
  });

  // Download all
  $('#download-all-accepted-apps').on('click', function() {
    $(this).text('Downloading...');
    const self = this;

    $.ajax({
      method: 'GET',
      url: $(this).data('url'),
      data: $(this).data('next'),
      success: function(res) {
        $(self).text('Download All as CSV');

        if (res.status === 'success') {
          const filename = 'TA App - All Accepted Applications ' + getToday() + '.csv';
          downloadCSV(res.data, filename);
        } else {
          const message = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' +
                            'An error occurred while downloading all data' +
                            '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>' +
                          '</div>';
          $('#download-csv-message').html(message);
        }
      },
      error: function(err) {
        $(self).text('Download All as CSV');

        const message = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' +
                          'Error: ' + err.statusText + ' (' + err.status + '). ' + err.responseJSON.message +
                          '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>' +
                        '</div>';
        $('#download-csv-message').html(message);
      }
    });

  });

});


// Get a table header
function getHeader(rows) {
  let header = [];
  for (let i = 0; i < rows[0].children.length-1; i++) {
    let row = rows[0].children[i];
    header.push( (row.className === 'sortable') ? replaceNewLine(row.children[0].innerText) : replaceNewLine(row.innerText) );
  }
  return header;
}


// Convert a form data to json
function formDataToJson(data) {
  let json = {};
  for (let obj of JSON.parse(data)) {
    if (obj['name'] === 'tasm') {
      json[ obj['name'] ] = (obj['value'] === 'on') ? true : false;
    } else {
      json[ obj['name'] ] = (obj['value'].length > 0) ? obj['value'] : null;
    }
  }
  return json;
}

// Sort column
function sortColumn(col, type='alpha', method='onclick') {
  const table = $("#accepted-apps-table")[0];
  const rows = table.rows;
  const arrRows = [...rows];

  let items = arrRows.slice(1, arrRows.length);
  let order;

  const header = rows[0].children[col];
  let headerIcon = header.children[1].children[0];

  // header menu
  for (let j = 0; j < rows[0].children.length; j++) {
    let headerCol = rows[0].children[j];

    if (headerCol.className === 'sortable') {
      let icon = headerCol.children[1].children[0];

      if (icon.classList.contains('fa-sort-numeric-asc')) icon.classList.remove('fa-sort-numeric-asc');
      else if (icon.classList.contains('fa-sort-numeric-desc')) icon.classList.remove('fa-sort-numeric-desc');
      else if (icon.classList.contains('fa-sort-alpha-asc')) icon.classList.remove('fa-sort-alpha-asc');
      else if (icon.classList.contains('fa-sort-alpha-desc')) icon.classList.remove('fa-sort-alpha-desc');

      icon.classList.add('fa-sort');
    }
  }

  if (sessionStorage.getItem('sortable-table')) {
    const data = JSON.parse(sessionStorage.getItem('sortable-table'));
    if (data.col === col) {
      if (method === 'onclick') {
        if (data.order === 'asc') order = 'desc';
        else order = 'asc';
      } else {
        order = data.order;
      }
    } else {
      order = 'asc';
    }
  } else {
    order = 'asc';
  }

  headerIcon.classList.remove('fa-sort');
  if (type === 'numeric' || type === 'date' || type === 'dollar') {
    if (order === 'asc') headerIcon.classList.remove('fa-sort-numeric-desc');
    if (order === 'desc') headerIcon.classList.remove('fa-sort-numeric-asc');
    headerIcon.classList.add('fa-sort-numeric-' + order);

  } else if (type === 'alpha') {
    if (order === 'asc') headerIcon.classList.remove('fa-sort-alpha-desc');
    if (order === 'desc') headerIcon.classList.remove('fa-sort-alpha-asc');
    headerIcon.classList.add('fa-sort-alpha-' + order);
  }

  // Merge sort
  if (order === 'asc') {
    items = sort(items, col, type);
  } else {
    if (method === 'sessionStorage') items = sort(items, col, type);
    items = items.reverse();
  }

  // Build
  build(table, items);

  // Add column information into local storage
  sessionStorage.setItem( 'sortable-table', JSON.stringify({ 'col': col, 'type': type, 'order': order }) );
}

function build(table, items) {
  let tbody = table.tBodies[0];
  while (tbody.firstChild)
    tbody.removeChild(tbody.firstChild);

  for(let i = 0; i < items.length; i++)
    tbody.appendChild(items[i]);
}

function sort(items, col, type) {
  if (items.length <= 1) return items;

  let mid = Math.floor(items.length / 2),
      left = sort(items.slice(0, mid), col, type),
      right = sort(items.slice(mid), col, type);

  return merge(left, right, col, type);
}

function merge(arr1, arr2, col, type) {
  let sorted = [];
  while (arr1.length && arr2.length) {
    if (getValue(arr1[0], col, type) < getValue(arr2[0], col, type) ) sorted.push(arr1.shift());
    else sorted.push(arr2.shift());
  };
  return sorted.concat(arr1.slice().concat(arr2.slice()));
};

function getValue(item, col, type) {
  const rawValue = (item.children[col].children.length === 0) ? item.children[col].innerText : item.children[col].children[0].innerText;

  let value;
  if (type === 'numeric') {
    value = ( isNaN(rawValue) ) ? -1 : Number(rawValue);
  } else if (type === 'date') {
    value = Date.parse(rawValue);
  } else if (type === 'dollar') {
    const num = rawValue.substring(1, rawValue.length);
    value = ( isNaN(num) ) ? -1 : Number(num);
  } else {
    value = rawValue.toLowerCase().replace(/\n/g, " ");
  }

  return value;
}

// Select worktag options
function selectWorktag(option_id) {
  const sp = option_id.split('_');
  const id = sp[1];
  const select_value = $('#' + option_id).val();
  let worktag = $('#id_worktag_' + id).val().trim();
  let is_checked = $('#' + option_id).is(':checked');

  if (is_checked) {
    if (worktag.length > 0) {
      worktag += ', ' + select_value
    } else {
      worktag = select_value
    }
    $('#id_worktag_' + id).val(worktag);
  } else {
    const worktag_sp = worktag.split(',');
    let new_worktag = [];
    for (let i = 0; i < worktag_sp.length; i++) {
      const item = worktag_sp[i].trim();
      if (item !== select_value) {
        new_worktag.push(item);
      }
    }
    $('#id_worktag_' + id).val(new_worktag.join(', '));
  }

}
