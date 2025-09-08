$(document).ready(function () {
  // check if contains container fo validation
  if ($('#validation-modal').length > 0) {
    // add validate button only for change form, we can recognize that by delete button
    if ($('.compile-vcl')) {
      var templateId = parseTemplateId();
      $("[name=_vcl_validate]").click(function (event) {
        var commandId = Date.now().toString(36) + Math.random().toString(36).substring(2);
        event.preventDefault();
        clearModal(commandId);
        vclValidateCommand(
          $('textarea[name=content]').val(),
          '/api/v0.1/vcl_template/' + templateId + '/vcl-validate-command/' + commandId + '/'
        );
      });
    }
  }
})

function clearModal(commandId) {
  $('#spinner').show();
  $('#result').hide();
  $('#command-status').removeClass();
  $('#command-status').addClass('badge badge-light').text("unknown");
  $('#command-result').removeClass();
  $('#command-result').addClass('badge badge-light').text("UNKNOWN");
  $('#validation-modal').modal('show');
  $('#command-id').text(commandId);
  $('#command-id').data("status", "started");
}

function parseTemplateId() {
  var linkParts = document.URL.split('/')
  return linkParts[linkParts.length - 3]
}

function vclValidateCommand(content, url) {
  return $.ajax({
    type: 'PUT',
    url: url,
    data: JSON.stringify({ 'content': content }),
    dataType: 'json',
    contentType: "application/json; charset=utf-8",
    error: handleErrorResponse,
    success: handleVclValidateResponse,
    beforeSend: setCRSFToken,
    complete: function () { if (isResultStillAwaited(url)) { setTimeout(function () { poolVclValidateResult(url) }, 500) } },
  });
}

function poolVclValidateResult(url) {
  $.ajax({
    url: url,
    dataType: 'json',
    error: handleErrorResponse,
    success: handleVclValidateResponse,
    complete: function () { if (isResultStillAwaited(url)) { setTimeout(function () { poolVclValidateResult(url) }, 500) } },
    timeout: 5000
  });
}

function handleErrorResponse(request, textStatus, errorThrown) {
  const status = data.status;
  setCommandStatus('done');
  console.error(textStatus, errorThrown)
  $('#command-result').removeClass().addClass(`badge-${statusToClass(validationStatus(false))}`).text(validationStatus('Error'));
  $('#error-type').text('Validation error')
  $('#error-message').text(request.responseText)
  $('#result').show();
  $('#spinner').hide();
  $('#command-status').removeClass().addClass(`badge badge-${statusToClass(status)}`).text('error');
}

function handleVclValidateResponse(data, textStatus, request) {
  const status = data.status;
  if (checkCommandStatus(data.pk, 'done')) return;
  if (status === 'FAILURE') {
    setCommandStatus('done');
    $('#spinner').hide()
  }
  else if (status === 'SUCCESS') {
    setCommandStatus('done');
    $('#servers-no').text(data.output.servers_num);
    $('#command-result').removeClass().addClass(`badge badge-${statusToClass(validationStatus(data.output.is_valid))}`).text(validationStatus(data.output.is_valid));
    if (!data.output.is_valid) {
      $('#error-type').text(data.output.error.type)
      $('#error-message').text(data.output.error.message)
      $('#result').show();
    }
    $('#spinner').hide()
  }
  $('#command-status').removeClass().addClass(`badge badge-${statusToClass(status)}`).text(status);
}

function validationStatus(status) {
  if (status) {
    return 'SUCCESS';
  }
  return 'FAIL';
}

function checkCommandStatus(status) {
  return $('#command-id').data('status') == status
}

function setCommandStatus(status) {
  $('#command-id').data('status', status)
}

function isPollingFinished(commandId, status) {
  return $('#command-id').text() != commandId || checkCommandStatus('done')
}

function isResultStillAwaited(commandURL) {
  var parts = commandURL.split('/')
  return !isPollingFinished(parts[parts.length - 2], 'done');
}
