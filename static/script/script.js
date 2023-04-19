$(function() {
    $('#datepicker').datepicker({format: 'dd/mm/yyyy'});

});

function changeState() {
    document.getElementById("description-text").disabled =! document.getElementById("description-text").disabled;
}
