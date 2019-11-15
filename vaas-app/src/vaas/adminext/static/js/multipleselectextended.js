(function ($) {
    window.addEventListener('load', (event) => {

        function displayDate() {
            console.log(SelectBox.cache.szymon_to)
        }

        document.getElementById("szymon_add_link").addEventListener("click", displayDate);
        document.getElementById("szymon_remove_link").addEventListener("click", displayDate);
        document.getElementById("szymon_add_all_link").addEventListener("click", displayDate);
        document.getElementById("szymon_remove_all_link").addEventListener("click", displayDate);
        document.getElementById("szymon_from").addEventListener("dblclick", displayDate);
        document.getElementById("szymon_to").addEventListener("dblclick", displayDate);
    });


})(django.jQuery);

