$(function () {
    'use strict'

    $('#inicial').datepicker({
        format: 'YYYY/mm/dd'
    });
    $('#final').datepicker({
        format: 'YYYY/mm/dd'
    });

    $('#inicial').on("change", function() {

        if($('#inicial').val() != "" && $('#final').val() != "") {
                
                $("#reportes_form").submit();

        }
    });

    $('#final').on("change", function() {
        
        if($('#inicial').val() != "" && $('#final').val() != "") {
                
                $("#reportes_form").submit();

        }

    });

    $('select').on('change', function () {

        if ($("#selecclonar").val() != "") {

            let now = new Date();

            let day = ("0" + now.getDate()).slice(-2);
            let month = ("0" + (now.getMonth() + 1)).slice(-2);

            let today = now.getFullYear() + "/" + (month) + "/" + (day);
            // let today = (day) + "/" + (month) + "/" + now.getFullYear();

            if($('#inicial').val() == "" || $("#selecclonar").val() == 'hoy')
                $('#inicial').val(today);
            if($('#final').val() == "" || $("#selecclonar").val() == 'hoy')
                $('#final').val(today);

        } else {
            $('#inicial').val("");
            $('#final').val("");
        }

        if ($("#localidad").val() != "" || $("#nombre_pv").val() != "" || $("#selecclonar").val() != "") {

            if($('#inicial').val() != "" && $('#final').val() != "") {
                
                $("#reportes_form").submit();

            }
                

        } else if ($("#localidad").val() == "" && $("#nombre_pv").val() == "") {

            $("#reportes_form").submit();

        }
    });


});
