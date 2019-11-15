(function($) {
window.addEventListener('load', (event) => {

    $('#szymon_to').change(function( ) {
        $('#szymon_to option').each(function() {
            console.log($(this).val())
         })
    });

    // var box = document.getElementById('szymon_to');
    // console.log(box);
  });
})(django.jQuery);

