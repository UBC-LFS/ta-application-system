$(document).ready(function() {

  // Download a csv file for a summary report
  $('#download-summary-report-csv').on('click', function() {
    const table = $("#summary-report-table")[0];
    const rows = table.rows;
    const header = getHeader(rows);
    let tableData = header.join(',') + '\n';

    for (let i = 1; i < rows.length; i++) {
       let rowData = '';
       for (let j = 1; j < rows[i].children.length; j++) {
         let col = rows[i].children[j];
         rowData += '"' + col.innerText + '",';
       }
       tableData += rowData.substring(0, rowData.length - 1) + '\n';
     }

     const filename = $(this).data('year') + ' TA Application Summary Report ' + getToday() + '.csv';
     downloadCSV(tableData, filename);
  });

});


// Get a table header
function getHeader(rows) {
  let header = [];
  for (let i = 1; i < rows[0].children.length; i++) {
    let row = rows[0].children[i];
    header.push( replaceNewLine(row.innerText) );
  }
  return header;
}
