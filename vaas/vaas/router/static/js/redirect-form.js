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
    let domain = $("[name=condition_0]").find(":selected").text(),
        current = $("[name=priority]").val(),
        redirect_id = 0;

    if (window.location.href.includes("change")) {
        redirect_id = window.location.href.split("/")[6];
    }
    refreshOptions($("[name=priority]"), `/router/redirect/priorities/${domain}/${redirect_id}/${current}/`)
}

$(function() {
    $("[name=condition_0]").change(function () {
        reloadPriorities();
    });
    reloadPriorities();
});
