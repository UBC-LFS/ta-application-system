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
        $(self).text('All');

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
        $(self).text('All');

        const message = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' +
                          'Error: ' + err.statusText + ' (' + err.status + '). ' + err.responseJSON.message +
                          '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>' +
                        '</div>';
        $('#download-message').html(message);
      }
    });
  });

  /* Download LFS Grad */
  $('#download-lfs-grad').on('click', function() {
    $(this).text('Downloading...');
    const self = this;

    $.ajax({
      method: 'GET',
      url: $(this).data('url'),
      data: $(this).data('next'),
      success: function(res) {
        $(self).text('LFS Grad');

        if (res.status === 'success') {
          const filename = 'TA App - LFS Grad ' + getToday() + '.csv';
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
        $(self).text('LFS Grad');

        const message = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' +
                          'Error: ' + err.statusText + ' (' + err.status + '). ' + err.responseJSON.message +
                          '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>' +
                        '</div>';
        $('#download-message').html(message);
      }
    });
  });

  /* Download past LFS TA */
  $('#download-past-lfs-ta').on('click', function() {
    $(this).text('Downloading...');
    const self = this;

    $.ajax({
      method: 'GET',
      url: $(this).data('url'),
      data: $(this).data('next'),
      success: function(res) {
        $(self).text('past LFS TA');

        if (res.status === 'success') {
          const filename = 'TA App - past LFS TA ' + getToday() + '.csv';
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
        $(self).text('past LFS TA');

        const message = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' +
                          'Error: ' + err.statusText + ' (' + err.status + '). ' + err.responseJSON.message +
                          '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>' +
                        '</div>';
        $('#download-message').html(message);
      }
    });
  });

});
