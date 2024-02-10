$(document).ready(function() {

  $('#save-changes').on('click', function(e) {
    console.log('here');
    const formData = $('#student-profile-form').serializeArray();
    const data = formDataToJson(JSON.stringify(formData));
    console.log(data);
    $.ajax({
          method: 'POST',
          url: $(this).data('url'),
          data: formDataToJson(JSON.stringify(formData)),
          dataType: 'json',
          success: function(res) {
            console.log('success', res);
            if (res.status === 'success') {

            } else {
              console.log('error', res.message);
              const message = '<div class="alert alert-danger alert-dismissible fade show text-left" role="alert">' +
                        res.message +
                        '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>';

              $('#save-changes-message').html(message);
            }

          },
          error: function(err) {
            console.log('error');
          },
          complete: function(jqXHR, textStatus) {
            console.log('complete');
          }
        });

  });

})


// Convert a form data to json
function formDataToJson(data) {
  let json = {};
  for (let obj of JSON.parse(data)) {
    json[ obj['name'] ] = (obj['value'].length > 0) ? obj['value'] : null;
  }
  return json;
}
