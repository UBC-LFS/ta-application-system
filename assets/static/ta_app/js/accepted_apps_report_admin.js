$(document).ready(function() {

  $('#download-all-accepted-apps-report-admin').on('click', function() {
    $(this).text('Downloading...');
    const self = this;

    $.ajax({
      method: 'GET',
      url: $(this).data('url'),
      data: $(this).data('next'),
      success: function(res) {
        $(self).text('Download All as CSV');

        if (res.status === 'success') {
          const filename = 'TA App - Report - Accepted Applications ' + getToday() + '.csv';
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
