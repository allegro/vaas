function validateCommand(url, content={}) {
    return $.ajax({
      type: 'PUT',
      url: url,
      data: JSON.stringify(content),
      dataType: 'json',
      contentType: "application/json; charset=utf-8",
      error: handleErrorResponse,
      success: handleCommandValidateResponse,
      beforeSend: setCRSFToken,
      complete: function () { if (isResultStillAwaited(url)) { setTimeout(function () { poolCommandResult(url) }, 500) } },
    });
}

function poolCommandResult(url) {
    $.ajax({
        url: url,
        dataType: 'json',
        error: handleErrorResponse,
        success: handleCommandValidateResponse,
        complete: function () { if (isResultStillAwaited(url)) { setTimeout(function () { poolCommandResult(url) }, 500) } },
        timeout: 5000
    });
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
    return !isPollingFinished(parts[parts.length-2], 'done');
}