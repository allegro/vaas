$(document).ready(function () {
    const clusters_in_sync = $('#id_clusters_in_sync');
    if (clusters_in_sync.is(":checked")) {
        $(".field-clusters").hide()
    }
    clusters_in_sync.change(function(){
        if ($(this).is(':checked')) {
            $(".field-clusters").hide()
        } else {
            $(".field-clusters").show()
        }
    });
});

