window.object_id = undefined


$(document).ready ->
  $ '.toolbar .toggle-search'
    .on 'click', () ->
      $('.leftsidelist div:first').slideToggle()

window.hashInformation = () ->
    params = {}
    for param in location.hash.replace('#','').split('&')
      params[param.split('=')[0]] = param.split('=')[1]
    return {hash:location.hash, params:params}

$(document).ready ->

  tab_id = $('#detail').parent('.tab-pane').attr('id')
  objectListId = $('#object-list').parent('.tab-pane').attr('id')
  detailTab = $("a[href='##{tab_id}']")
  listTab = $("a[href='##{objectListId}']")

  $.fn.hideHelpText = () ->
    name = this.attr 'name'
#    console.log "Hide help text for #{name}"
#    console.log $("hint_id_#{name}")
    $("#hint_id_#{name}").hide()

  selects = $('.search-form select')
  if $.isFunction selects.select2
    selects.select2()
    selects.each ->
      $(this).next().css
        'width': '95%'
        'max-height': '40px;'
      if $(this).val()
        id = $(this).attr('id')
        s = '[href="#div_' + id + '"]'
        $(s).trigger 'click'
      return
  else
    console.warn 'select2 isn\'t working - maybe library is not loaded!'


  $searchInputs = $('form.search-form .nav input[checked]')
  # This is too
  $searchInputs.parents('label.btn').addClass 'active'
  # Build a hash of selected filters
  filters = {}
  filter_buttons = $searchInputs.parents('label.btn').each(->
    t = $(this).text()
    cat = $(this).parents('')
    if filters[t] == undefined
      filters[t] = [ t ]
    $('body').append $(this).text()
    return
  )
  # If a search is active, hide any nonselected items BUT add a "Show more / less..." button
  $searchInputs.parent('label').siblings().not('.active').hide()
  $searchInputs.parents('.collapse').addClass('in').attr 'aria-expanded', 'true'
  b = $('<a href="#" class="btn btn-primary btn-xs"><span class="glyphicon glyphicon-plus"></span></a>').insertBefore($searchInputs.parents('div [data-toggle=buttons]'))
  b.on 'click', ->
    $(this).siblings('div:first').find('label').not('.active').toggle()
    return


  $('.auto-select2').select2().hideHelpText()
  $('.auto-multiselect').multiselect().hideHelpText()
  $('.auto-chosen').chosen().hideHelpText()


  $('[data-chosenurl]').each () ->
    url = $(this).data('chosenurl')
    $(this).ajaxChosen({dataType: 'json',type:'GET', url: url})
    $(this).hideHelpText()


  $('[data-selecturl]').each () ->
    $(this).select2
      ajax:
        url: $(this).data('selecturl')
        delay: 250
      minimumInputLength: 3
    $(this).hideHelpText()

  # Set which tab should be active
  if window.location.search.search('page') > -1 or window.location.search.search('sort') > -1
    listTab.tab('show')
  else if window.location.hash.search('object') > -1
    detailTab.tab('show')

  # If NO tab is active yet, make the first tab active
  $('#object-tabs li:first a').tab('show') if $('#object-tabs li.active').length == 0

  # Include a "click" handler on object href's
  $(document).on 'click', 'a[href^="#object"]', () ->
    detailTab.tab('show')

  # On moving to detail tab load the first object if nothing is present yet
  detailTab.on 'show.bs.tab', (e) ->
    href = $(e.target).attr('href')
    if $(href).children('#detail').length > 0

      if window.hashInformation().params['object'] is undefined
        window.location.hash = $('a[href^="#object"]:first').attr('href')

loadDetailFromHash = () ->
  tab_id = $('#detail').parent('.tab-pane').attr('id')
  detailTab = $("a[href='##{tab_id}']")
  hash = hashInformation()

  get = () ->
    if $(document).width() <= 992 and $('#detail').length isnt 0
      $('html,body').animate({scrollTop:$('#detail').offset().top}, 200)

    hash = hashInformation()
    window.get_object_id
    if hash.params['object']
      $('li.object').removeClass 'active'

      $('#detail').stop().fadeOut(400, ()->
        if (typeof($.fn.waiting) == 'function')

          $('#rightpane .loading').remove()
          d = $('<div>').addClass('loading').appendTo('#rightpane').waiting()
          d.waiting('play')
      )

      link = $('[href="#object=' + hash.params.object + '"]').parent('li').addClass 'active'

      $.get './' + hash.params.object + '/ajax/', (data) ->
        $('#detail').html data
        $('#detail').stop().fadeIn(400)
        $('#rightpane .loading').remove()
        detailTab.tab('show')


  if hash.params['object'] != object_id and hash.params['object'] isnt undefined
    detailTab.parent('li').removeClass('disabled')
    get()
  else
    detailTab.parent('li').addClass('disabled')
    $('a[href="#list-tab"]').tab('show')

  window.object_id = hashInformation().params['object']
#  get()

$(window).on 'hashchange', () ->

  # Search for "last" and "next" buttons and populate with appropriate primary keys
  # This is necessary because our DetailView doesn't know about the filtered list it is called from
  loadDetailFromHash()
  if window.object_list is undefined
    console.warn 'object_list is undefined!'
    return

$(document).on 'click', 'form button', (e) ->
  window.location.hash = ''

$(document).on 'click', '.object-next', (e) ->
  e.preventDefault()
  window.location.hash = '#object='+window.object_list[window.hashInformation().params.object].next

$(document).on 'click', '.object-last', (e) ->
  e.preventDefault()
  window.location.hash = '#object='+window.object_list[window.hashInformation().params.object].last

window.setPage = (page) ->
  # Set the page number
    # Page number can't go below 1

    pages = $('span[data-page]').not('[data-page=next]').not('[data-page=previous]')
    this_page = $('span[data-page=' + page + ']')
    page_info = $('.pagination [data-currentpage]')

    pages.hide()
    this_page.show()
    page_info.text page
    page_info.data 'currentpage', page


paginateResults = (groupSize) ->
  # groupSize = 15
  l = $('.list-group')
  i = 0
  while l.children('.list-group-item').length > 0
    i += 1
    text = groupSize * i + ' to ' + groupSize * i + groupSize
    l.children('li').slice(0, groupSize).wrapAll '<span data-page="' + i + '" data-text="' + text + '">'
  $('span[data-page]').hide()
  $('.pagination [data-pages]').text i
  $('span[data-page=1]').show()
  $('.pagination').data 'page', 1
  new_page = undefined
  page_info = $('.pagination [data-currentpage]')
  page_info.text '1'
  page_info.data 'currentpage', 1

  $('a[data-page]').on 'click', (e)->
    e.preventDefault()
    current_page = page_info.data('currentpage')
    action = $(this).data('page')
    setPage(current_page + 1) if action is "next" and current_page < i
    setPage(current_page - 1) if action is "previous" and current_page > 1

    return false
  $('#organizationSelect').multiselect enableCollapsibleOptGroups: true
  $('#inactiveOrganizationSelect').multiselect {}
  # $('#organizationSelect').next().find('.multiselect-group input').remove();
  return

# Injection of an AJAX form into a Bootstrap Modal to create a more linear, one-page user experience

$(document).ready ->
#  setSelections()

  $.fn.selectToHidden = () ->
    console.log($(this))
    # Find any "select" with a SINGLE option and convert this to a label instead
    $(this).find('select').each () ->
      if $(this).children('option').length == 1
        # Replaces fields which should be "readonly" (eg changing the Location from a Project -
        # only the Location should be changeable
        # TODO: Determine which SELECT fields should be hidden
        #
        return

        console.log 'hiding'
        $(this).parents('label').hide().addClass('hidden')

        thisname = $(this).prop('name')
        thisvalue = $(this).val()

        $("<input type='hidden' name='#{thisname}' value='#{thisvalue}'>").appendTo($(this).parents('form'))
        $(this).parents('.form-group').remove()



  loadDetailFromHash()
#  paginateResults(15)

  # $.fn.ajaxModal = (url, title, callback, successRedirect, reload) ->
  $.fn.ajaxModal = (options) ->
    if $.isFunction($.simplyToast)
      $.simplyToast('<p><b>Loading</b></p><p>Retrieving form from database, please wait....</p>')

    defaults =
      successRedirect: false
      callback: false
      container: false

    options = $.extend(defaults, options);

    console.log options

    url = options.url
    if options.url is undefined
      console.error('Form load URL was undefined')
      return
    modal = $(this)
    if options.container
      modal.addClass 'container'
    modal.find('.modal-header h4').text(options.title)

    # Change the modal content to a loading indicator
    modal.find('.modal-body').text('')
    d = $('<div>').addClass('loading').appendTo(modal.find('.modal-body')).waiting()
    d.waiting('play')

    request = $.get options.url
      .done () ->
        d.waiting('pause')
        d.hide()
        f = $(request.responseText)
        f.selectToHidden()
        console.log "$.get(#{url}) done"

        f.append($('<div class="input-group input-group-sm"><span class="input-group-addon" id="basic-addon2">Your name</span><input id="form-name" name="_name" class="form-control"></div>'))
        .append($('<div class="input-group input-group-sm"><span class="input-group-addon" id="basic-addon2">Email address</span><input name="_email" class="form-control" ></label></div>'))
        .append($('<div class="input-group input-group-sm"><span class="input-group-addon" id="basic-addon2">Comments</span><input name="_comment" class="form-control"></label></div>'))

        f.find('[name=_name]').val(localStorage.user_name)
        f.find('[name=_email]').val(localStorage.user_email)

        f.find('.form-actions').hide()

        modal.find('.modal-body').append f
        f.formSetAdd()
        console.log 'Appended form to body'

        # ------------------------------- Plugins
#        Enable autolookup fields for select
        f.find('[data-selecturl]').each () ->
          console.log $(this)

          $(this).select2
            ajax:
              url: $(this).data('selecturl')
              delay: 250
            minimumInputLength:3
            allowClear: true
            width: '100%'

          $(this).hideHelpText()
          $(this).on 'select2:open', () ->
            $('.select2-container--open').css
              zIndex: 10000

        f.find('[data-selecttwo]').each () ->
          if $.isFunction $.fn.multiselect
            $(this).multiselect()

        f.find('.selectmultiple').not('[data-selecturl]').each () ->
          if $.isFunction $.fn.multiselect
            $(this).multiselect()
            $(this).hideHelpText()

        # 'trumbowyg.js' integration for rich HTML editing

        f.find('.trumbowyg').each () ->
          if $.isFunction $.fn.trumbowyg
            $(this)
              .trumbowyg()
              .on 'dblclick', () ->
                $(this).trumbowyg
                  lang: 'en',
                  closable: true,
                  mobile: true,
                  fixedBtnPane: true,
                  fixedFullWidth: true,
                  semantic: true,
                  resetCss: true,
                  autoAjustHeight: true,
                  autogrow: true

            $(this).css('padding-top', $(this).find('ul:trumbowyg-button-pane').css('height'))


        f.find('.summernote').each () ->
          if $.isFunction $.fn.summernote
            $(this).summernote()

          else
            console.warn 'Requested a jquery plugin which was not loaded: trumbowyg'

        # ---------- End of plugins


        modal.find('.apply_datepicker').each () ->
          console.log 'Call datepicker'
          $(this).Zebra_DatePicker()
          # Fix icon positioning
          modal.find('.Zebra_DatePicker_Icon').css(
            left:'9px'
          )

        modal.off 'click', '.btn#modal-form-delete'
        modal.off 'click', '.modal-footer .btn-primary'

        # Making testing easier by adding the "from-url" as a parameter

        modal.find('.modal-footer .btn-primary').attr('data-fromurl', options.url)

        modal.on 'click', '.modal-footer .btn-primary', () ->
          # Rudimentary validation handler for the form
          validated = true
          console.log ('validation')
          f.css(
            border: '1px solid red'
            )
#          Code below FAILS for multilingual forms!
#          modal.find $('.requiredField').each ->
#            if modal.find('#'+$(this).attr('for')).val() is ""
#              validated = false
#              console.log('validation failed')
#              console.log $(this)
#              console.log $('#'+$(this).attr('for'))
#              $(this).parents('.form-group').addClass('has-error')
#          return if not validated

          f.ajaxSubmit()
          xhr = f.data('jqxhr')

          xhr.success () ->


            if options.success
              success = options.success
              if $.isFunction success
                success(xhr.responseJSON)
              else if $.isFunction window[success]
                window[success](xhr.responseJSON)
              else
                console.warn("callback #{success} failed - not a function")

            if $.isFunction($.simplyToast)
              $.simplyToast('<p><b>Suggestion Received</b></p><p>The database team will review your change soon!</p>')
            else
              console.log 'simplyToast function is not available'

            if xhr.responseJSON.success_url and options.reload # Load a success_url address, if provided, to change page on a successful submission
              console.log xhr.responseJSON.success_url
              document.location.href = xhr.responseJSON.success_url
              location.reload(true)
            localStorage.user_name = f.find('[name=_name]').val()
            localStorage.user_email = f.find('[name=_email]').val()

            modal.modal('hide')

          xhr.error () ->
            $.simplyToast('<p><b>Suggestion Error</b></p><p>There was a problem with this request</p>', 'danger')
        $('modal #modal-form-delete').off('click')
        modal.on 'click', '.btn#modal-form-delete', (e) ->
          console.log "Modal Delete triggered"
          e.preventDefault()
      #    d = $('#modalform form').serializeArray()
          modal.find('form').ajaxSubmit({
          url: "/suggest/suggest/"
          success:  ->
            xhr = $('.modal.in form').data('jqxhr');
            $.simplyToast('<p><b>Remove Request Received</b></p><p>The database team will review your change soon!</p>', 'warning')
            $('.modal.in').modal('hide')
          error: ->
            $.simplyToast('<p><b>Suggestion Error</b></p><p>There was a problem with this request</p>', 'danger')
          })

        modal.modal()

        modal.on 'hidden.bs.modal', () ->
          if options.destroyOnComplete
            # modal.modal('destroy')
            modal.parent('.modal-scrollable').remove()
            modal.remove()

        modal.on 'shown.bs.modal', () ->

          if options.callback
            callback = options.callback
            if $.isFunction callback
              callback()
            else if $.isFunction $.fn[callback]
              $(modal)[callback]()
            else if $.isFunction window[callback]
              window[callback]()
            else
              console.warn("callback #{callback} failed - not a function")

      .error () ->
        if d
          d.waiting 'pause'
          d.hide()

        a = $('<div>').addClass('alert alert-warning')
        a.text("There was a problem getting data from the server. This form is not available right now.")

        modal.find('.modal-body').append a
        modal.modal()



  loadModalDeleteForm = (url, title) ->

    console.log 'loadModalDeleteForm triggered'
    $('#modaldeleteform').ajaxModal(url, title)

  loadModalForm = (url, title) ->

    console.log 'loadModalForm triggered'
    $('#modalform').ajaxModal(url, title)

  $(document).on 'click', '.modal-form-load', (e) ->
    alert('obsolete: use data-modalurl instead')
    console.log '.modal-form-load clicked'
    e.preventDefault();
    loadModalForm($(this).attr('href'), $(this).data('modaltitle'))

  $(document).on 'click', '.modal-deleteform-load', (e) ->
    alert('obsolete: use data-modalurl instead')
    console.log '.modal-deleteform-load clicked'
    e.preventDefault();
    loadModalDeleteForm($(this).attr('href'), $(this).data('modaltitle'))

  $(document).on 'click', '[data-modalurl]', (e) ->
    e.preventDefault()

    modal = $( $(this).data('modalselector') || '#modalform')
    # modal = modal_template.clone(false).removeAttr("id")

    options =
      url : $(this).data('modalurl')
      title : $(this).data('modaltitle') or 'Changes'
      callback : $(this).data('modalcallback') || false
      reload : $(this).data('reload') || false
      container : $(this).data('container') || false

      # window.location : $(this).data('next') if $(this).data('next')
      successRedirect : $(this).data('modalnext') if $(this).data('modalnext') or undefined
    console.log options
    $(modal).ajaxModal(options)

  $.fn.formSetAdd = () ->
    console.log 'Adding addition buttons for URL selection'
    console.log($(this))
    $(this)
      .find '[data-add-modalurl]'
      .each () ->
        console.log($(this))
        $e = $(this)
        $e.css
          width: '60%'
        console.log('Creating lookup')
        setAdded = (suggestion, label) ->

          su = "_#{suggestion}_"

          console.log("Successfully triggered setAdded: #{suggestion} #{label}")
          console.log $e.prop('tagName')
          if $e.prop('tagName') is 'SELECT'
            # $e.children().remove()
            # TODO: Append option (if select)
            o = $('<option>')
            o.attr('selected', 'selected')
            o.attr('value', su)
            o.text(label)

            console.log ('appending')
            console.log $e
            console.log o
            $e.append(o)

            $e.select2("destroy");
            # Rebuild:
            $e.select2
              ajax:
                url: $e.data('selecturl')
                delay: 250
              minimumInputLength:3
              allowClear: true
            $e.css
              width: '60%'
            # $e.append(<option selected=selected value='_'+suggestion+'_')

          if $e.prop('tagName') is 'INPUT'
            $e.val(suggestion)

        $e = $(this)
        d = $(this).data('add-displayfield') || false
        cb = () ->
          return

        if d
          cb = (rj) ->
            setAdded(rj['id'], JSON.parse(rj['data'])[d])
            # return {'suggestion':suggestion,'label': rj['data'][d]}
        else
          cb = (rj) ->
            setAdded(rj['id'], 'New item')

        opts =
          url : $(this).data('add-modalurl')
          title : 'Create New'
          successRedirect : false
          success: cb
          destroyOnComplete:true

        modal = $('#modalform')
          .clone()
          .removeAttr('id')

        $("<a href=#{opts.url}>")
          .addClass 'btn btn-sm btn-default'
          .css
            width: '35%'
          .on 'click', (e) ->
            e.preventDefault()
            console.log 'loading secondary Create selector'
            $(modal).ajaxModal(opts)
          .text('Create New')
          .insertAfter($(this))


        return false

#$(document).ready ->
#  setSelections()
#  $('.chosen-container').css
#    'width':'100%'

$(document).ready ->
  top = $("#object-tabs").offset().top
  $(window).on 'resize', () ->
    top = $("#object-tabs").offset().top

  $(window).on 'scroll', () ->
    if $(window).scrollTop() > top
      $("#object-tabs").addClass('sticky')
    else
      $("#object-tabs").removeClass('sticky')

$(document).ready ->
  showPlace = () ->

$(document).ready ->
  $('a[data-postform]').on 'click', (e) ->
    link = $(this)
    e.preventDefault()
    form = $($(this).data('postform'))
    console.log(form)
    xhr = $.post $(form).attr('action'),  $(form).serializeArray()
    xhr.done () ->
      window.open(link.prop('href'))
    xhr.fail () ->
      new_form = $(xhr.responseText)
      new_form.append(form.find('input[name=csrfmiddlewaretoken]'))
      form.replaceWith new_form
