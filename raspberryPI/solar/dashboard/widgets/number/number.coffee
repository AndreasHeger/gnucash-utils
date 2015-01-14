class Dashing.Number extends Dashing.Widget
  @accessor 'current', Dashing.AnimatedValue

  @accessor 'difference', ->
    if @get('last')
      last = parseFloat(@get('last'))
      # use value (not rounded)
      current = parseFloat(@get('value'))
      if last != 0
        diff = Math.abs(current - last)
        if diff >= 0.01
          "#{diff.toFixed(2)} C"
    else
      ""

  @accessor 'arrow', ->
    if @get('last')
      last = parseFloat(@get('last'))
      # use value (not rounded)
      current = parseFloat(@get('value'))
      if (last != 0)
        if (Math.abs(current - last) >= 0.01)
          if current > last then 'icon-arrow-up' else 'icon-arrow-down'

  onData: (data) ->
    if data.status
      # clear existing "status-*" classes
      $(@get('node')).attr 'class', (i,c) ->
        c.replace /\bstatus-\S+/g, ''
      # add new class
      $(@get('node')).addClass "status-#{data.status}"
