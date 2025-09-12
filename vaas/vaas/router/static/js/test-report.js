class ReportGateway {
  constructor(url, renderResults) {
    this.commandId = Date.now().toString(36) + Math.random().toString(36).substring(2);
    this.url = url + this.commandId + "/";
    this.renderResults = renderResults

    $('#spinner').show();
    $('#results').text("");
    $('#pass-count').text(0);
    $('#failed-count').text(0);
    $('#error-message').remove();
    $('#command-status').removeClass();
    $('#command-status').addClass(`badge badge-default`).text("UNKNOWN");
    $('#command-result').removeClass();
    $('#command-result').addClass(`badge badge-default`).text("UNKNOWN");
    $('#command-id').text(this.commandId);
    $('#command-id').data("status", "started");
  }

  order() {
    return $.ajax({
      type: 'PUT',
      url: this.url,
      data: '{}',
      dataType: 'json',
      contentType: "application/json; charset=utf-8",
      error: (request, textStatus, errorThrown) => { this.handleErrorResponse(request, textStatus, errorThrown) },
      success: (data, textStatus, request) => { this.handleSuccessResponse(data, textStatus, request) },
      beforeSend: setCRSFToken,
      complete: () => { this.complete() },
    });
  }

  pollResult() {
    $.ajax({
      url: this.url,
      dataType: 'json',
      error: (request, textStatus, errorThrown) => { this.handleErrorResponse(request, textStatus, errorThrown) },
      success: (data, textStatus, request) => { this.handleSuccessResponse(data, textStatus, request) },
      complete: () => { this.complete() },
      timeout: 5000
    });
  }

  complete() {
    if (this.isResultStillAwaited()) {
      setTimeout(() => { this.pollResult() }, 500)
    }
  }

  handleSuccessResponse(data, textStatus, request) {
    const status = data.status;
    if (this.checkCommandStatus('done')) return;
    if (status === 'FAILURE') {
      this.setCommandStatus('done');
      this.showError("Can't generate report. Task failed. Refresh page and try again")
    }
    else if (status === 'SUCCESS') {
      this.setCommandStatus('done');
      $('#results').append(this.renderResults(data.output.validation_results));
      $('#pass-count').text(this.countResult('PASS', data.output.validation_results));
      $('#failed-count').text(this.countResult('FAIL', data.output.validation_results));
      $('#command-result').addClass(`badge-${statusToClass(data.output.validation_status)}`).text(data.output.validation_status);
    }
    $('#spinner').hide();
    $('#command-status').removeClass();
    $('#command-status').addClass(`badge badge-${statusToClass(status)}`).text(status);
  }

  countResult(resultString, records) {
    var counter = 0;
    records.forEach(function (record) {
      if (record.result === resultString) {
        counter += 1
      }
    })
    return counter;
  }

  handleErrorResponse(request, textStatus, errorThrown) {
    this.setCommandStatus('done');
    console.error(textStatus, errorThrown);
    $('#command-details').append(`<div id="error-message" class="alert alert-danger" role="alert">${request.responseText || errorThrown}</div>`);
    $('#command-result').addClass(`badge-${statusToClass('FAIL')}`).text(validationStatus('Error'));
    $('#spinner').hide();
  }

  showError(message) {
    $('#error-message').remove();
    $('#command-details').append(`<div id="error-message" class="alert alert-danger" role="alert">${message}</div>`);
  }

  isResultStillAwaited() {
    return $('#command-id').text() == this.commandId && !this.checkCommandStatus('done');
  }

  setCommandStatus(status) {
    $('#command-id').data('status', status);
  }

  checkCommandStatus(status) {
    return $('#command-id').data('status') == status
  }
}

function initReport(url, reportGenerator) {
  var testResultModalEl = $('#testResultModal');
  testResultModalEl.on('show.bs.modal', function (event) {
    let reportGateway = new ReportGateway(url, reportGenerator);
    reportGateway.order();
  });
}
