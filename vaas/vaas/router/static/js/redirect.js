const noDataPlaceholder = { name: 'no data', id: 'no data' };
function redirectsValidateCommand(url) {
    return $.ajax({
        type: 'PUT',
        url: url,
        data: '{}',
        dataType: 'json',
        contentType: "application/json; charset=utf-8",
        error: handleErrorResponse,
        success: handleRedirectsValidateResponse,
        beforeSend: setCRSFToken,
        complete: function () { if (isResultStillAwaited(url)) { setTimeout(function () { poolRedirectsValidateResult(url) }, 500) } },
    });
}

function poolRedirectsValidateResult(url) {
    $.ajax({
        url: url,
        dataType: 'json',
        error: handleErrorResponse,
        success: handleRedirectsValidateResponse,
        complete: function () { if (isResultStillAwaited(url)) { setTimeout(function () { poolRedirectsValidateResult(url) }, 500) } },
        timeout: 5000
    });
}

function handleRedirectsValidateResponse(data, textStatus, request) {
    const status = data.status
    if (checkCommandStatus('done')) return;
    if (status === 'FAILURE') {
        setCommandStatus('done');
        showError("Can't generate report. Task failed. Refresh page and try again")
        $('#spinner').hide()
    }
    else if (status === 'SUCCESS') {
        setCommandStatus('done');
        $('#results').append(createTestResult(data.output.validation_results))
        $('#pass-count').text(countResult('PASS', data.output.validation_results));
        $('#failed-count').text(countResult('FAIL', data.output.validation_results));
        $('#command-result').addClass(`label-${statusToClass(data.output.validation_status)}`).text(data.output.validation_status);
        $('#spinner').hide()
    }
    $('#command-status').removeClass();
    $('#command-status').addClass(`label label-${statusToClass(status)}`).text(status);
}

function createTestResult(records) {
    var html = '';
    records.sort(function(x, y) {
    if (x.error_message && !y.error_message) {
    return -1;
    }
    if (!x.error_message && y.error_message) {
    return 1;
    }
    if (x.expected.redirect.id < y.expected.redirect.id) {
    return -1;
    }
    return 1;
    });
    console.log(records)
    records.forEach(function (record) {
        var errorMsg = ''
        if (!record.current.redirect) record.current.redirect = noDataPlaceholder
        if (record.error_message) errorMsg = `<div class="alert alert-danger" role="alert">${record.error_message}</div>`
        html += `<div class="panel panel-${statusToClass(record.result)}">
            <div class="panel-heading">
            <h3 class="panel-title">${record.url}</h3>
            </div>
            <div class="panel-body">
            ${errorMsg}
            <div class="row">
                <div class="col-md-6">
                <div class="panel panel-default">
                    <div class="panel-body">
                    <h5><strong>Location:</strong> <code>${record.current.location}</code></h5>
                    <h6 class="text-muted">redirect.contition: ${record.current.redirect.name}</h6>
                    <h6 class="text-muted">redirect.id: ${record.current.redirect.id}</h6>
                    </div>
                    <div class="panel-footer">
                    Current
                    </div>
                </div>
                </div>
                <div class="col-md-6">
                    <div class="panel panel-default">
                    <div class="panel-body">
                        <h5><strong>Location:</strong> <code>${record.expected.location}</code></h5>
                        <h6 class="text-muted">redirect.contition: ${record.expected.redirect.name}</h6>
                        <h6 class="text-muted">redirect.id: ${record.expected.redirect.id}</h6>
                    </div>
                    <div class="panel-footer">
                        Excpeted
                    </div>
                    </div>
                </div>
            </div>
            </div>
        </div>`
    });
    return html
}

function countResult(resultString, records) {
    var counter = 0;
    records.forEach(function (record) {
        if (record.result === resultString) {
        counter += 1
        }
    })
    return counter;
}

function handleErrorResponse(request, textStatus, errorThrown) {
    setCommandStatus('done');
    console.error(textStatus, errorThrown)
    $('#command-details').append(`<div id="error-message" class="alert alert-danger" role="alert">${request.responseText || errorThrown}</div>`)
    $('#command-result').addClass(`label-${statusToClass('FAIL')}`).text(validationStatus('Error'));
    $('#spinner').hide();
}

function showError(message) {
    $('#error-message').remove()
    $('#command-details').append(`<div id="error-message" class="alert alert-danger" role="alert">${message}</div>`)
}

function isPollingFinished(commandId, status) {
    return $('#command-id').text() != commandId || checkCommandStatus('done')
}

function isResultStillAwaited(commandURL) {
    var parts = commandURL.split('/')
    return !isPollingFinished(parts[parts.length - 2], 'done');
}

function setCommandStatus(status) {
    $('#command-id').data('status', status)
}

function checkCommandStatus(status) {
    return $('#command-id').data('status') == status
}

function clearModal(commandId) {
    $('#spinner').show();
    $('#results').text("");
    $('#pass-count').text(0);
    $('#failed-count').text(0);
    $('#error-message').remove();
    $('#command-status').removeClass();
    $('#command-status').addClass(`label label-default`).text("unknown");
    $('#command-result').removeClass();
    $('#command-result').addClass(`label label-default`).text("UNKNOWN");
    $('#command-id').text(commandId);
    $('#command-id').data("status", "started");
}