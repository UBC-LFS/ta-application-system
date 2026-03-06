$(document).ready(function() {

  $('#download-job-total-ta-hours').on('click', function() {
     $(this).text('Downloading...');
     const self = this;

     $.ajax({
       method: 'GET',
       url: $(this).data('url'),
       data: $(this).data('next'),
       success: function(res) {
         $(self).text('Total TA Hours');

         if (res.status === 'success') {
           const filename = 'TA App - Job Info - Total TA Hours ' + getToday() + '.xlsx';
           downloadExcel(res.data, filename);
         } else {
           displayMessage('#download-message');
         }
       },
       error: function(err) {
         $(self).text('Total TA Hours');
         displayErrorMessage(err, 'download-message');
       }
     });
  });

  $('#download-job-instructors').on('click', function() {
     $(this).text('Downloading...');
     const self = this;

     $.ajax({
       method: 'GET',
       url: $(this).data('url'),
       data: $(this).data('next'),
       success: function(res) {
         $(self).text('Instructors');

         if (res.status === 'success') {
           const filename = 'TA App - Job Info - Instructors ' + getToday() + '.xlsx';
           downloadExcel(res.data, filename);
         } else {
           displayMessage('#download-message');
         }
       },
       error: function(err) {
         $(self).text('Instructors');
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
