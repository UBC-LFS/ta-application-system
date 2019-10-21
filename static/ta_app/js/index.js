$(document).ready(function () {
  console.log("js ready");
  var contentHeight = $("#content").height()
  var screenHeight = $(window).height();
  if (contentHeight > screenHeight) {
    document.getElementById("footer").style.marginTop = contentHeight + "px";
  } else {
    var defaultHeight = screenHeight - 140;
    document.getElementById("footer").style.marginTop = defaultHeight + "px";
  }



  function onElementHeightChange(elm, callback) {
    var lastHeight = elm.clientHeight, newHeight;
    (function run() {
      newHeight = elm.clientHeight;
      if (lastHeight != newHeight)
        callback();
      lastHeight = newHeight;

      if (elm.onElementHeightChangeTimer)
        clearTimeout(elm.onElementHeightChangeTimer);

      elm.onElementHeightChangeTimer = setTimeout(run, 200);
    })();
  }


  onElementHeightChange(document.getElementById("content"), function () {
    var contentHeight = $("#content").height()
    var screenHeight = $(window).height();
    if (contentHeight > screenHeight) {
      document.getElementById("footer").style.marginTop = contentHeight + "px";
    } else {
      var defaultHeight = screenHeight - 140;
      document.getElementById("footer").style.marginTop = defaultHeight + "px";
    }
  });

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
