$(document).ready(function () {
  console.log(window.location.href);
  if (window.location.href.indexOf("administrators") > -1) {
    document.getElementById('admin').classList.add("active");
  } else {
    if (document.getElementById('admin')) {
      document.getElementById('admin').classList.remove("active");
    }
  }

  if (window.location.href.indexOf("human_resources") > -1) {
    document.getElementById('hr').classList.add("active");
  } else {
    if (document.getElementById('hr')) {
      document.getElementById('hr').classList.remove("active");
    }
  }

  if (window.location.href.indexOf("instructors") > -1) {
    document.getElementById('instructor').classList.add("active");
  } else {
    if (document.getElementById('instructor')) {
      document.getElementById('instructor').classList.remove("active");
    }
  }

  if (window.location.href.indexOf("students") > -1) {
    document.getElementById('student').classList.add("active");
  } else {
    if (document.getElementById('student')) {
      document.getElementById('student').classList.remove("active");
    }
  }

  $('#nav-tab a[data-toggle="tab"]').on('click', function(e) {
    e.preventDefault();
    window.localStorage.setItem('activeTab', $(e.target).attr('href'));
  });

  var activeTab = window.localStorage.getItem('activeTab');
  if (activeTab) {
    $('#nav-tab a[href="' + activeTab + '"]').tab('show');
  }

  $('#btn-logout').on('click', function(e) {
    e.preventDefault();
    window.localStorage.removeItem("activeTab");
  });

});
