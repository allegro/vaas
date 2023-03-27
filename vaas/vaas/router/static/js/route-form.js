function getChosenClusters() {
    let cluster_query = "";
    SelectBox.cache.id_clusters_to.forEach((e, idx) => {
        cluster_query += `clusters=${e.value}`;
        if (idx < (SelectBox.cache.id_clusters_to.length - 1)) {
            cluster_query += "&";
        }
    });
    return cluster_query;
}

function reloadPriorities() {
    let director_id = $("[name=director]").val() || 0,
        current = $("[name=priority]").val(),
        clusters_sync = $("#id_clusters_in_sync").is(":checked"),
        route_id = 0;

    if (window.location.href.includes("change")) {
        route_id = window.location.href.split("/")[6];
    }
    refreshOptions($("[name=priority]"), `/router/route/priorities/${director_id}/${route_id}/${current}/?${getChosenClusters()}${clusters_sync ? `&clusters_sync=${clusters_sync}` : ''}`)
}

function initForm() {
    // wait until select-picker is ready before initialize
    if (SelectBox.cache.id_clusters_to === undefined) {
        setTimeout(initForm, 100)
        return
    }
    let clusters_in_sync = $("#id_clusters_in_sync");
    if (clusters_in_sync.is(":checked")) {
        $(".field-clusters").hide();
    }
    clusters_in_sync.change(function(){
        if ($(this).is(":checked")) {
            $(".field-clusters").hide();
        } else {
            $(".field-clusters").show();
        }
        reloadPriorities();
    });
    // override original function that is called as effect of many different events
    // instead of adding custom listener for each event
    // original js: /static/admin/js/SelectBox.js
    SelectBox.move = (function(original) {
        return function(from, to) {
            original(from, to);
            reloadPriorities();
        };
    })(SelectBox.move);
    SelectBox.move_all = (function(original) {
        return function(from, to) {
            original(from, to);
            reloadPriorities();
        };
    })(SelectBox.move_all);
    $("[name=director]").change(function () {
        clusters_in_sync.prop("disabled", $(this).find(":selected").text() === "---------");
        reloadPriorities();
    });
    reloadPriorities();
}

// delay adding listeners until clusters widget is ready
$(function() {
    initForm();
});
