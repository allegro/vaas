function refreshOptions(selector, url) {
    $.ajax(
        {
            url: url,
            success: function (result) {
                selector.find('option').remove();
                result['values'].forEach(
                    function (value) {
                        var options = "<option value='" + value + "'>" + value + "</option>";
                        selector.append(options);
                    }
                );
                selector.val(result['choose']);
            }
        }
    );
}