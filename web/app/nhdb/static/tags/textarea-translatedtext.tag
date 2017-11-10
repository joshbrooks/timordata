<textarea-translatedtext>
    <p>Translated Text</p>

    <p>{opts.pk}</p>
    <p>{opts.field}</p>

    <button onclick='{change_language}' each="{lang_name, lang_code in window.languages}">
        {lang_name} {lang_code}
    </button>

    <form>
      <div>
        <label each={lang_name, lang_code in window.languages} for={opts.field+'_'+language+'_'+opts.pk}">{opts.field} {language}</label>
        <textarea ref="{lang_code}" class="form-control" id="{opts.field+'_'+language+'_'+opts.pk}">{}</textarea>
      </div>
    </form>
    <button onclick="{save}">Save</button>
    <p>{JSON.stringify(content)}</p>

    <script>
        var tag = this;
        tag.contents = '';
        tag.language = 'en';

        tag.on('mount', function(){
            tag.language = tag.opts.language || 'en'; // initial value
            tag.opts.table.get(_.toInteger(opts.pk)).then(function(d) {
                tag.update({original: d[opts.field]});
                tag.trigger('change-language', tag.language);
            })
        });
        tag.save = function(e){tag.trigger('save', e)};
        tag.on('save', function(){
            var n = {};
            _(tag.refs).each(function(i,j){_.set(n, [tag.opts.field, j], i.value)});
            tag.opts.table.update(_.toInteger(tag.opts.pk), n).then(function (updated) {
              if (updated)
                console.log ("Friend number 2 was renamed to Number 2");
              else
                console.log ("Nothing was updated - there were no friend with primary key: 2");
            });
        });

        tag.change_language = function(e){tag.trigger('change-language', e.item.lang_code)};

        tag.on('change-language', function(l){tag.update({language: l, contents: tag.original});})
    </script>

</textarea-translatedtext>