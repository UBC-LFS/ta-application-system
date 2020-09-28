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
           str += replaceNewLine(col.children[0].innerText) + '",';
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

   exportCSV(tableData);
 });

});

// Get today's date format
function getToday() {
  const d = new Date();
  let month = d.getMonth();
  if (month < 10) month = '0' + d.getMonth();
  let date = d.getDate();
  if (date < 10) date = '0' + d.getDate();
  return d.getFullYear() + '-' + month + '-' + date;
}

// Export data to a csv file
function exportCSV(data) {
  let el = document.createElement('a');
  const blob = new Blob([data], { type: 'text/csv; charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  el.href = url;
  el.setAttribute('download', 'TA App - Accepted Applications ' + getToday() + '.csv');
  el.click();
}


// Get a table header
function getHeader(rows) {
  let header = [];
  for (let i = 0; i < rows[0].children.length-1; i++) {
    let row = rows[0].children[i];
    header.push( (row.className === 'sortable') ? replaceNewLine(row.children[0].innerText) : replaceNewLine(row.innerText) );
  }
  return header;
}

function replaceNewLine(str) {
  return str.trim().replace(/\n/g, ' ');
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

/*****************************/

/*
function sortColumn2(col, type='alpha', order='asc') {
  var t0 = performance.now();

  const table = $("#accepted-apps-table")[0];
  const rows = table.rows;

  // Find an existing icon
  for (let j = 0; j < rows[0].children.length; j++) {
    let headerCol = rows[0].children[j];

    if (headerCol.className === 'sortable') {
      let icon = headerCol.children[1].children[0];
      if (icon.classList.contains('fa-sort-numeric-asc')) {
        icon.classList.remove('fa-sort-numeric-asc');
        icon.classList.add('fa-sort');
      }
      else if (icon.classList.contains('fa-sort-numeric-desc')) {
        icon.classList.remove('fa-sort-numeric-desc');
        icon.classList.add('fa-sort');
      }
      else if (icon.classList.contains('fa-sort-alpha-asc')) {
        icon.classList.remove('fa-sort-alpha-asc');
        icon.classList.add('fa-sort');
      }
      else if (icon.classList.contains('fa-sort-alpha-desc')) {
        icon.classList.remove('fa-sort-alpha-desc');
        icon.classList.add('fa-sort');
      }
    }
  }

  const header = rows[0].children[col];
  let icon = header.children[1].children[0];
  icon.classList.remove('fa-sort');

  let keepSwitching = true;
  let isSwitched = false;
  let count = 0;

  while (keepSwitching) {

    if (type === 'numeric' || type === 'date' || type === 'dollar') {
      if (order === 'asc') icon.classList.remove('fa-sort-numeric-desc');
      if (order === 'desc') icon.classList.remove('fa-sort-numeric-asc');
      icon.classList.add('fa-sort-numeric-' + order);

    } else if (type === 'alpha') {
      if (order === 'asc') icon.classList.remove('fa-sort-alpha-desc');
      if (order === 'desc') icon.classList.remove('fa-sort-alpha-asc');
      icon.classList.add('fa-sort-alpha-' + order);
    }

    keepSwitching = false;
    let i, a, b;
    for (i = 1; i < (rows.length - 1); i++) {
      isSwitched = false;
      a = (rows[i].children[col].children.length === 0) ? rows[i].children[col].innerText : rows[i].children[col].children[0].innerText;
      b = (rows[i + 1].children[col].children.length === 0) ? rows[i + 1].children[col].innerText : rows[i + 1].children[col].children[0].innerText;
      const [first, second] = getValidItem(type, a, b);
      // console.log(a, b);

      if (order === 'asc') {
        if (first > second) {
          isSwitched = true;
          break;
        }
      } else if (order === 'desc') {
        if (first < second) {
          isSwitched = true;
          break;
        }
      }
    }

    if (isSwitched) {
      rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
      keepSwitching = true;
      count++;
    } else {
      if (count === 0 && order === 'asc') {
        order = 'desc';
        keepSwitching = true;
      }
    }

    // Add column information into local storage
    sessionStorage.setItem( 'sortable-table', JSON.stringify({ 'col': col, 'type': type, 'order': order }) );
  }
  var t1 = performance.now();
  console.log("It took " + (t1 - t0) + " milliseconds.");
}

function getValidItem(type, a, b) {
  if (type === 'numeric') {
    a = ( isNaN(a) ) ? -1 : Number(a);
    b = ( isNaN(b) ) ? -1 : Number(b);
  } else if (type === 'date') {
    a = Date.parse(a);
    b = Date.parse(b);
  } else if (type === 'dollar') {
    num_a = a.substring(1, a.length);
    num_b = b.substring(1, b.length);
    a = ( isNaN(num_a) ) ? -1 : Number(num_a);
    b = ( isNaN(num_b) ) ? -1 : Number(num_b);
  } else {
    a = a.toLowerCase().replace(/\n/g, " ");
    b = b.toLowerCase().replace(/\n/g, " ");
  }
  return [a, b];
}
*/
