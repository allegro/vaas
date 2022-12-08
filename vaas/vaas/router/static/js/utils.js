function countResult(resultString, records) {
    var counter = 0;
    records.forEach(function (record) {
        if (record.result === resultString) {
        counter += 1
        }
    })
    return counter;
}

function showError(message) {
    $('#error-message').remove()
    $('#command-details').append(`<div id="error-message" class="alert alert-danger" role="alert">${message}</div>`)
}
