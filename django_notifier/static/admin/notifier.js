django.jQuery(function($) {

    $(document).on('change', '.js-variables-switcher', function(event) {
        $('.js-variables-item').hide(0);
        $('#' + $(this).val()).show(0);

        var excludedRecipient = $('#' + $(this).val()).data('excludedRecipient');

        if (excludedRecipient !== undefined) {
            $('.js-recipient-switcher')
                .find('[value="#' + excludedRecipient + '#"]')
                .attr('disabled', '');
            $('.js-recipient-switcher')
                .find('option')
                .first()
                .attr('selected', 'selected');
        };
    });

});