function ScormStudioXBlock(runtime, element) {
  var handlerUrl = runtime.handlerUrl(element, "studio_submit");

  $(element)
    .find(".save-button")
    .bind("click", function () {
      var form_data = new FormData();
      var scorm_file = $(element).find("#scorm_file_field").val();
      var display_name = $(element).find("#display_name_field").val();
      var has_score = $(element).find("#has_score_field").val();
      var width = $(element).find("#width_field").val();
      var height = $(element).find("#height_field").val();
      var popup = $(element).find("#popup_field").val();
      var autoopen = $(element).find("#autoopen_field").val();
      var allowopeninplace = $(element).find("#allowopeninplace_field").val();
      form_data.append("scorm_file", scorm_file);
      form_data.append("display_name", display_name);
      form_data.append("has_score", has_score);
      form_data.append("width", width);
      form_data.append("height", height);
      form_data.append("popup", popup);
      form_data.append("autoopen", autoopen);
      form_data.append("allowopeninplace", allowopeninplace);
      runtime.notify("save", { state: "start" });

      $.ajax({
        url: handlerUrl,
        dataType: "text",
        cache: false,
        contentType: false,
        processData: false,
        data: form_data,
        type: "POST",
        success: function (data, textStatus, jqXHR) {
          runtime.notify("save", { state: "end" });
        },
        error: function (jqXHR, textStatus, errorThrown) {
          var error_field = JSON.parse(jqXHR.responseText).field;
          var error_message = JSON.parse(jqXHR.responseText).message;

          $("#" + error_field + "_field")
            .parent()
            .css("color", "red");
        },
      });
    });

  $(element)
    .find(".cancel-button")
    .bind("click", function () {
      runtime.notify("cancel", {});
    });
}
