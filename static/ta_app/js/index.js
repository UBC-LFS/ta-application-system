$(document).ready(function () {
  if (window.location.href.indexOf("administrators") > -1) {
    document.getElementById('admin').classList.add("active");
  } else {
    if (document.getElementById('admin')) {
      document.getElementById('admin').classList.remove("active");
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

});
