var template = "";
function showTimeProfile() {
    $("#fieldset-2").hide();
    $('#fieldset-timeprofile').show();
}

function showAdvancedOptions() {
    $('#fieldset-timeprofile').hide();
    $('#fieldset-2').show();
}

function switchProfile(enabled) {
    if(enabled) {
        showTimeProfile();
    } else {
        showAdvancedOptions();
    }
}

function loadProfile() {
    var director = $('#id_director').val();
    if (parseInt(director)>0) {
        $.get('/api/v0.1/director/' + $('#id_director').val() + "/", function(data) {
            $('#profile_name').text(data['time_profile']['name']);
            $('#profile_max_connections').val(data['time_profile']['max_connections']);
            $('#profile_connect_timeout').val(data['time_profile']['connect_timeout']);
            $('#profile_first_byte_timeout').val(data['time_profile']['first_byte_timeout']);
            $('#profile_between_bytes_timeout').val(data['time_profile']['between_bytes_timeout']);
        });
    }
}

$(document).ready(function () {
    $('#content-main > div').append('<fieldset class="_module _aligned" id="fieldset-timeprofile" style="background:transparent;display:none;"/>');
    $('#fieldset-timeprofile').load('/static/js/template-time-profile.html', function() {
        loadProfile();
    });

    $('#id_inherit_time_profile').click(function () {
       switchProfile(this.checked);
    });
    $('#id_director').change(function () {
        loadProfile();
    });

    switchProfile($('#id_inherit_time_profile').prop("checked"));
});