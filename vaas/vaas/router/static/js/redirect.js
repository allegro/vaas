var RaportRenderer = function (ref, raport) {
    this.ref = ref;
    this.raport = raport;

    this.show = function () { this.raport.render(this.ref); }
};


var Redirect = function (value) {
    this.value = value;

    this.createPanel = function (name, id, location, condition) {
        return `
        <div class="col-md-6">
            <div class="panel panel-default">
                <div class="panel-body">
                    <h5><strong>Location:</strong> <code>${location || 'no data'}</code></h5>
                    <h6 class="text-muted">redirect.contition: ${condition || 'no data'}</h6>
                    <h6 class="text-muted">redirect.id: ${id || 'no data'}</h6>
                </div>
                <div class="panel-footer">${name}</div>
            </div>
        </div>`
    }

    this.sortByErrors = function () {
        this.value.sort(function (x, y) {
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
    }

    this.renderError = function (error = '') {
        if (error != '') {
            return `<div class="alert alert-danger" role="alert">${error}</div>`
        }
        return error
    }

    this.render = function (ref) {
        this.sortByErrors()
        var html = '';
        this.value.forEach(function (record) {
            if (!record.current.redirect) record.current.redirect = { name: 'no data', id: 'no data' }
            html += `<div class="panel panel-${statusToClass(record.result)}">
                <div class="panel-heading">
                <h3 class="panel-title">${record.url}</h3>
                </div>
                <div class="panel-body">
                ${this.renderError(record.error_message)}
                <div class="row">
                    ${this.createPanel('Current', record.current.redirect.id, record.current.location, record.current.redirect.name)}
                    ${this.createPanel('Excpeted', record.expected.redirect.id, record.expected.location, record.expected.redirect.name)}
                </div>
            </div>`
        }, this);
        ref.append(html);
    }
};




function handleCommandValidateResponse(data, textStatus, request) {
    const status = data.status
    if (checkCommandStatus('done')) return;
    if (status === 'FAILURE') {
        setCommandStatus('done');
        showError("Can't generate report. Task failed. Refresh page and try again")
        $('#spinner').hide()
    }
    else if (status === 'SUCCESS') {
        setCommandStatus('done');
        createTestResult(data.output.validation_results)
        // $('#results').append(createTestResult(data.output.validation_results))
        $('#pass-count').text(countResult('PASS', data.output.validation_results));
        $('#failed-count').text(countResult('FAIL', data.output.validation_results));
        $('#command-result').addClass(`label-${statusToClass(data.output.validation_status)}`).text(data.output.validation_status);
        $('#spinner').hide()
    }
    $('#command-status').removeClass();
    $('#command-status').addClass(`label label-${statusToClass(status)}`).text(status);
}

function createTestResult(records) {
    var redirect = new Redirect(records);
    var raport = new RaportRenderer($('#results'), redirect)
    raport.show();
}

function handleErrorResponse(request, textStatus, errorThrown) {
    setCommandStatus('done');
    console.error(textStatus, errorThrown)
    $('#command-details').append(`<div id="error-message" class="alert alert-danger" role="alert">${request.responseText || errorThrown}</div>`)
    $('#command-result').addClass(`label-${statusToClass('FAIL')}`).text(validationStatus('Error'));
    $('#spinner').hide();
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