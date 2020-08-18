$(document).ready(function() {

  // Make a navigation header active
  const roles = window.location.pathname.split('/');
  if (roles[1] === 'administrators') {
    $('#nav-administrator').addClass('active');

  } else if (roles[1] === 'instructors') {
    $('#nav-instructor').addClass('active');

  } else if (roles[1] === 'students') {
    $('#nav-student').addClass('active');

  } else if (roles[1] === 'users') {

    const parameters = window.location.href.split('?');
    if ( parameters[1].includes('administrators') ) {
      $('#nav-administrator').addClass('active');

    } else if ( parameters[1].includes('instructors') ) {
      $('#nav-instructor').addClass('active');

    } else if ( parameters[1].includes('students') ) {
      $('#nav-student').addClass('active');
    }
  }

  // Remove admin docs data
  if ( sessionStorage.getItem('admin-docs') ) {
    const data = JSON.parse( sessionStorage.getItem('admin-docs') );
    $("#admin-docs-form-message").append(data.message);
    sessionStorage.removeItem('admin-docs');
  }

  // Summernote settings
  $('.summernote').summernote({
    height: 150,
    toolbar: []
  });

});
