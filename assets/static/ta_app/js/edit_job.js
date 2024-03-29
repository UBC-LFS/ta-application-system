$(document).ready(function() {

  // Search instructors
  $("#edit-job-form #input-instructor").on("input", function() {
    const username = $(this).val();
    if (username.length === 0) {
      $("#edit-job-form #display-instructors").children().remove();
    } else {
      $.ajax({
        method: 'GET',
        url: $(this).data('url'),
        data: { 'username': username, 'session_slug': $(this).data('session'), 'job_slug': $(this).data('job') },
        dataType: 'json',
        success: function(res) {
          if (res.status === 'success') {
            if (res.data.length > 0) {
              let instructors = '<ul class="search-result instructors">';
              for (let ins of res.data) {
                instructors += '<li data-select-instructor="' + ins.id + '">' + ins.username + ' ('+ ins.first_name + ' ' + ins.last_name + ')</li>';
              }
              instructors += '</ul>';
              $("#edit-job-form #display-instructors").html(instructors);
            } else {
              $("#edit-job-form #display-instructors").html('<div class="search-result"><p>No instructors found</p></div>');
            }
          }
        }
      });
    }
  });

  // Add instructors into a job
  $("#edit-job-form #display-instructors").on("click", 'ul.instructors > li', function() {
    $.ajax({
      method: 'POST',
      url: $(this).parent().parent().data('add-url'),
      data: {
        'instructors': $(this).attr('data-select-instructor'),
        'csrfmiddlewaretoken': $(this).parent().parent().data('form')
      },
      dataType: 'json',
      success: function(res) {
        let message = '<div class="alert alert-STATUS alert-dismissible fade show" role="alert">' + res.message + '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button></div>';

        if (res.status === 'success') message = message.replace('STATUS', 'success');
        else message = message.replace('STATUS', 'danger');

        const instructor = '<div class="instructor" data-instructor="' + res.user.username + '">' +
                              res.user.username + ' (' + res.user.first_name + ' ' + res.user.last_name + ')' +
                              '<button class="delete-instructor btn btn-danger btn-xs ml-2" type="button" data-id="' + res.user.id + '" data-delete-url="' + res.data.delete_url + '" data-form="' + res.data.csrfmiddlewaretoken + '">' +
                                '<i class="fa fa-times" aria-hidden="true"></i>' +
                              '</button>' +
                            '</div>';

        if ( $("#edit-job-form #job-instructors").children().length === 0 ) {
          $("#edit-job-form #job-instructors").html("");
        }
        $("#edit-job-form #job-instructors").append(instructor);
        $("#edit-job #delete-job-instructor-messages").append(message);
      }
    });
  });

  // Delete job instructors
  $("#edit-job-form #job-instructors").on("click", ".delete-instructor", function() {
    $.ajax({
      method: 'POST',
      url: $(this).data('delete-url'),
      data: { 'instructors': $(this).data('id'), 'csrfmiddlewaretoken': $(this).data('form') },
      dataType: 'json',
      success: function(res) {
        let message = '<div class="alert alert-STATUS alert-dismissible fade show" role="alert">' +
                        res.message +
                        '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>' +
                      '</div>';

        if (res.status === 'success') message = message.replace('STATUS', 'success');
        else message = message.replace('STATUS', 'danger');

        $("#edit-job-form #job-instructors").find("[data-instructor='" + res.username + "']").remove();
        if ( $("#edit-job-form #job-instructors").children().length === 0 ) {
          $("#edit-job-form #job-instructors").html("None");
        }
        $("#edit-job #delete-job-instructor-messages").append(message);
      }
    });
  });

});
