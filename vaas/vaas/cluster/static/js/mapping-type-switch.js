$(document).ready(function () {
    const mapping_type = $('#id_type');
    if (mapping_type.find(":selected").val() == "dynamic") {
        $(".field-clusters").hide()
    }
    // TODO(mfalkowski): probably OK,DONE
    mapping_type.change(function(){
        if ($(this).find(":selected").val() == "dynamic") {
            $(".field-clusters").hide()
        } else {
            $(".field-clusters").show()
        }
    });
});
