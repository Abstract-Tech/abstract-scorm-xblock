function ScormXBlock(runtime, element, settings) {
  function SCORM_12_API() {
    this.LMSInitialize = function () {
      return "true";
    };

    this.LMSFinish = function () {
      return "true";
    };

    this.LMSGetValue = GetValue;
    this.LMSSetValue = SetValue;

    this.LMSCommit = function () {
      return "true";
    };

    this.LMSGetLastError = function () {
      return "0";
    };

    this.LMSGetErrorString = function (errorCode) {
      return "Some Error";
    };

    this.LMSGetDiagnostic = function (errorCode) {
      return "Some Diagnostice";
    };
  }

  function SCORM_2004_API() {
    this.Initialize = function () {
      return "true";
    };

    this.Terminate = function () {
      return "true";
    };

    this.GetValue = GetValue;
    this.SetValue = SetValue;

    this.Commit = function () {
      return "true";
    };

    this.GetLastError = function () {
      return "0";
    };

    this.GetErrorString = function (errorCode) {
      return "Some Error";
    };

    this.GetDiagnostic = function (errorCode) {
      return "Some Diagnostice";
    };
  }

  var GetValue = function (cmi_element) {
    return $.ajax({
      type: "POST",
      url: runtime.handlerUrl(element, "scorm_get_value"),
      data: JSON.stringify({ name: cmi_element }),
      async: false,
    }).responseText;
  };

  var SetValue = function (cmi_element, value) {
    $.ajax({
      type: "POST",
      url: runtime.handlerUrl(element, "scorm_set_value"),
      data: JSON.stringify({ name: cmi_element, value: value }),
      async: true,
      success: function (response) {
        if (typeof response.lesson_score != "undefined") {
          $(".lesson_score", element).html(response.lesson_score);
        }
        $(".completion_status", element).html(response.completion_status);
      },
    });
  };

  var GetAPI = function () {
    let api;
    if (settings.scorm_version == "1.2") {
      api = new SCORM_12_API();
    } else {
      api = new SCORM_2004_API();
    }
    return api;
  };

  $(function ($) {
    let width = settings.scorm_xblock.width
      ? settings.scorm_xblock.width
      : screen.height;
    let height = settings.scorm_xblock.height;

    let innerIframe =
      "<!DOCTYPE html><html><head><style>body, html, * {width: 100%; height: 100%; margin: 0; padding: 0; border: 0;}</style></head><body>" +
      '<iframe class="scorm_object" src="' +
      settings.scorm_url +
      '" width="100%" height="100%" ' +
      'allow="fullscreen" allowFullScreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"></iframe>' +
      "</html></body>";
    let outerIframe =
      '<iframe class="scorm-iframe scorm_object" ' +
      'width="' +
      (settings.scorm_xblock.width ? settings.scorm_xblock.width + 5 : "100%") +
      '" ' +
      'height="' +
      (settings.scorm_xblock.height + 5) +
      '" ' +
      'allow="fullscreen" allowFullScreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"></iframe>';

    var popupWindow = null;

    function GoInFullscreen(element) {
      var p;
      if (element.requestFullscreen) p = element.requestFullscreen();
      else if (element.mozRequestFullScreen) p = element.mozRequestFullScreen();
      else if (element.webkitRequestFullscreen)
        p = element.webkitRequestFullscreen();
      else if (element.msRequestFullscreen) p = element.msRequestFullscreen();
      else p = Promise.reject();
      return p;
    }

    function GoOutFullscreen(element) {
      var p;
      if (element.ownerDocument.exitFullscreen)
        p = element.ownerDocument.exitFullscreen();
      else if (element.ownerDocument.mozCancelFullScreen)
        p = element.ownerDocument.mozCancelFullScreen();
      else if (element.ownerDocument.webkitExitFullscreen)
        p = element.ownerDocument.webkitExitFullscreen();
      else if (element.ownerDocument.msExitFullscreen)
        p = element.ownerDocument.msExitFullscreen();
      else p = Promise.reject();
      return p;
    }

    function detachHandler(element) {
      element.ownerDocument.removeEventListener("click", handleClick, true);
    }

    function handleClick(event) {
      let element = event.currentTarget.body;
      GoInFullscreen(element)
        .then(function () {
          GoOutFullscreen(element);
        })
        .then(function () {
          detachHandler(element);
        })
        .catch(function () {
          detachHandler(element);
        });
    }

    function showPopup(params) {
      if (popupWindow == null || popupWindow.closed) {
        console.log(params);
        popupWindow = window.open(
          "",
          settings.scorm_xblock.display_name,
          params
        );
        if (popupWindow) {
          popupWindow.document.open();
          popupWindow.API = popupWindow.API_1484_11 = GetAPI();
          popupWindow.document.write(innerIframe);
          popupWindow.document.close();
          setTimeout(function () {
            let i = popupWindow.frames[0];
            if (
              $.browser.mozilla &&
              i.mejs &&
              Object.keys(i.mejs.players).length > 0
            ) {
              i.document.addEventListener("click", handleClick, true);
            }
          }, 1000);
        }
        $(".scorm_popup_warning", element).show();
      } else {
        popupWindow.focus();
      }
    }

    function showIframe() {
      $(".scorm_window", element).replaceWith(outerIframe);
      let iframe = $(".scorm-iframe", element)[0];
      iframe =
        iframe.contentWindow ||
        iframe.contentDocument.document ||
        iframe.contentDocument;
      iframe.document.open();
      iframe.API = iframe.API_1484_11 = GetAPI();
      iframe.document.write(innerIframe);
      iframe.document.close();
    }
    var params =
      "width=" +
      (width + 5) +
      "px,height=" +
      (height + 5) +
      "px,top=" +
      (screen.height - height) / 2 +
      ",left=" +
      (screen.width - width) / 2 +
      ",resizable=yes,scrollbars=no,status=yes";
    if (settings.scorm_xblock.popup && settings.scorm_xblock.autoopen) {
      showPopup(params);
    } else if (!settings.scorm_xblock.popup) {
      showIframe();
    }
    $(".scorm_launch", element).on("click", function () {
      showPopup(params);
    });
    $(".scorm_show", element).on("click", function () {
      showIframe();
    });
  });
}
