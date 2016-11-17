
$(document).ready(function () {
    $(document).on('click', 'input.changelocations', function () {
        $('#map img').remove();
        // createMap function, from leaflet-location-setter, dynamically replaces a #map on the page with an 'editable' map
        createMap();
        $(this).attr('disabled', 'disabled');
        $(document).off('submit', 'form#update-projectplace').on('submit', 'form#update-projectplace', function (e) {
            e.preventDefault();
            returns = [];
            $.map(globalLayers, function (e, i) {
                returns.push({
                    "project": window.object(),
                    "place": globalLayers[i][0].feature.properties.pcode
                })
            });
            $(this).find('[name=data]').val(JSON.stringify({'projectplace_set': returns}));
            var xhr = $.post('/suggest/suggest/', $(this).serializeArray());
            if (xhr.success){
              if ($.isFunction($.simplyToast)) {

                $.simplyToast('<p><b>Suggestion Received</b></p><p>The database team will review your change soon!</p>');
              } else {
                console.log('simplyToast function is not available');
              }}

        })
    });
});



$(document).ready(function () {

    $('#toggle-object-list').on('click', function(){
    $('#object-list').css({position:'relative'}).animate({
  left: '-100%',
  position: 'relative',
  zIndex: '-1',
  opacity: '0'
})})
     })
