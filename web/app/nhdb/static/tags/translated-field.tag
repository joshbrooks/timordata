<translated-field>
    <p>{translatedString}<span class="small"> - {translationLanguage} ({_.join(tag_languages, ', ')})</span>  </p>

    <script>
        var tag = this;
        _.get(window, 'languages', ['en','tet','ind','pt']);
        tag.set_language = undefined;
        tag.tag_languages = [];

        tag.on('mount',function(){
            tag.tag_languages = _.keys(tag.opts.field);
            tag.trigger('setLanguage')});

        tag.on('setLanguage', function(){
            var translatedString;
            var translationLanguage;

            _.each(tag.tag_languages, function(l) {
                translatedString = _.get(tag.opts.field, l);
                translationLanguage = l;
                if (translatedString) {
                    return false;
                }
            });
            tag.update({translatedString:translatedString,translationLanguage:translationLanguage})
        });

        tag.setLanguage = function(){tag.trigger('setLanguage')}
    </script>
</translated-field>