$(document).ready(function () {
  console.log("js ready");

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

});
