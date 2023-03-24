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
    // prevent from reading select-picker if it is not initialized
    if (SelectBox.cache.id_clusters_to === undefined) {
        setTimeout(reloadPriorities, 100)
        return
    }
    let director_id = $("[name=director]").val() || 0,
        current = $("[name=priority]").val(),
        clusters_sync = $("#id_clusters_in_sync").is(":checked"),
        route_id = 0;

    if (window.location.href.includes("change")) {
        route_id = window.location.href.split("/")[6];
    }
    refreshOptions($("[name=priority]"), `/router/route/priorities/${director_id}/${route_id}/${current}/?${getChosenClusters()}${clusters_sync ? `&clusters_sync=${clusters_sync}` : ''}`)
}

// delay adding listeners until clusters widget is ready
$.when( $.ready ).then(function() {
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
    $("#id_clusters_add_link").click(reloadPriorities);
    $("#id_clusters_remove_link").click(reloadPriorities);
    $("#id_clusters_add_all_link").click(reloadPriorities);
    $("#id_clusters_remove_all_link").click(reloadPriorities);
    // TODO handle listening on cluster changes by clicking them
    $("[name=director]").change(function () {
        clusters_in_sync.prop("disabled", $(this).find(":selected").text() === "---------");
        reloadPriorities();
    });
    reloadPriorities();
});
