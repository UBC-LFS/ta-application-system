$(document).ready(function() {

  $('#download-job-report-md').on('click', function() {
     $(this).text('Downloading...');
     const self = this;

     $.ajax({
       method: 'GET',
       url: $(this).data('url'),
       data: $(this).data('next'),
       success: function(res) {
         $(self).text('Markdown');

         if (res.status === 'success') {
           const filename = 'TA App - Job Report ' + getToday() + '.md';
           downloadMarkdown(res.data, filename);
         } else {
           displayMessage('#download-message');
         }
       },
       error: function(err) {
         $(self).text('Markdown');
         displayErrorMessage(err, 'download-message');
       }
     });
   });

  $('#download-job-report-excel').on('click', function() {
    $(this).text('Downloading...');
    const self = this;

    $.ajax({
      method: 'GET',
      url: $(this).data('url'),
      data: $(this).data('next'),
      success: function(res) {
        $(self).text('Excel');

        if (res.status === 'success') {
          const filename = 'TA App - Job Report ' + getToday() + '.xlsx';
          downloadExcel(res.data, filename);
        } else {
          displayMessage('#download-message');
        }
      },
      error: function(err) {
        $(self).text('Excel');
        displayErrorMessage(err, 'download-message');
      }
    });
  });

});


function displayMessage(id_tag) {
  const message = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' +
                    'An error occurred while downloading all data' +
                    '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>' +
                  '</div>';
  $(id_tag).html(message);
}
