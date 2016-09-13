$(document).ready(function() {
    $('.selectize').selectize({
        plugins: ['remove_button'],
        persist: false,
        closeAfterSelect: true,
        openOnFocus: false,
        selectOnTab: true,
        maxOptions: 5,
    });
});
