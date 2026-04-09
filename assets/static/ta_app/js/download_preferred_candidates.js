$(document).ready(function() {

  /* Download all applications */
  $('#download-all-apps').on('click', function() {
    $(this).text('Downloading...');
    const self = this;

    $.ajax({
      method: 'GET',
      url: $(this).data('url'),
      data: $(this).data('next'),
      success: function(res) {
        $(self).text('Download All');

        if (res.status === 'success') {
          const filename = 'TA App - All Applications ' + getToday() + '.xlsx';
          downloadExcel(res.data, filename);
        } else {
          const message = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' +
                            'An error occurred while downloading all data' +
                            '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>' +
                          '</div>';
          $('#download-message').html(message);
        }
      },
      error: function(err) {
        $(self).text('Download All');

        const message = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' +
                          'Error: ' + err.statusText + ' (' + err.status + '). ' + err.responseJSON.message +
                          '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>' +
                        '</div>';
        $('#download-message').html(message);
      }
    });
  });


  /* Download preferred candidates */
  $('#download-preferred-candidates').on('click', function() {
    $(this).text('Downloading...');
    const self = this;

    $.ajax({
      method: 'GET',
      url: $(this).data('url'),
      data: $(this).data('next'),
      success: function(res) {
        $(self).text('Download Preferred Candidates');

        if (res.status === 'success') {
          const filename = 'TA App - Preferred Candidates ' + getToday() + '.csv';
          downloadCSV(res.data, filename);
        } else {
          const message = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' +
                            'An error occurred while downloading all data' +
                            '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>' +
                          '</div>';
          $('#download-message').html(message);
        }
      },
      error: function(err) {
        $(self).text('Download Preferred Candidates');

        const message = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' +
                          'Error: ' + err.statusText + ' (' + err.status + '). ' + err.responseJSON.message +
                          '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>' +
                        '</div>';
        $('#download-message').html(message);
      }
    });
  });
});
