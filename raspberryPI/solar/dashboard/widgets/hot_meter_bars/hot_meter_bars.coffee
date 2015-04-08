class Dashing.HotMeterBars extends Dashing.Widget

  @accessor 'title'

  ready: ->
    @drawWidget( @get('meter_items') )

  onData: (eventData) ->
    @drawWidget(eventData.meter_items)

  drawWidget: (meter_items) ->
    container = $(@node)
    rowsContainer = container.find('.rows-container')

    if meter_items.length == 0
      rowsContainer.empty()
    else
      # Float value used to scale the rows to use the entire space of
      # the widget
      rowHeight = 100 / meter_items.length
      counter = 0
      @clearIntervals()

      # Add or move rows for each project. Checks first if the row
      # already exists.
      meter_items.forEach (item) =>
        normalizedItemName = item.name.replace(/\W+/g, "_")
        referenceRow = rowsContainer.children().eq(counter)
        existingRow = rowsContainer.find("."+normalizedItemName)

        if existingRow.length
          if referenceRow.attr("class").indexOf(normalizedItemName) == -1
            existingRow.detach().insertBefore(referenceRow)
            existingRow.hide().fadeIn(1200)
        else
          row = createRow(item)
          if referenceRow.length
            row.insertBefore(referenceRow)
          else
            rowsContainer.append(row)
          row.hide().fadeIn(1200)

        elem = rowsContainer.find("."+normalizedItemName+" .inner-hot-meter-bar")
        if elem.length
          @animateMeterBarContent(elem[0], item, 1000)
        ++counter

      # Remove any nodes that were not in the new data, these will be
      # the rows at the end of the widget.
      currentNode = rowsContainer.children().eq(counter-1)
      while currentNode.next().length
        currentNode = currentNode.next()
        currentNode.fadeOut(100, -> $(this).remove() )

      # Set the height after rows were added/removed.
      rows = rowsContainer.children()
      percentageOfTotalHeight = 100 / meter_items.length
      applyCorrectedRowHeight(rows, percentageOfTotalHeight)

      if @zebra
        applyZebraStriping(rows)


  #***/
  # Create a JQuery row object with the proper structure and base
  # settings for the item passed in.
  #
  # The Row DOM Hierarchy:
  # Row
  #   Row Content (here so we can use vertical alignment)
  #     Project Name
  #     Outer Bar Container (The border and background)
  #       Inner Bar Container (The meter and text)
  #
  # @item - object representing an item and it's meter
  # /
  createRow = (item) ->

    row = ( $("<div/>")
      .attr("class", "row " + item.name.replace(/\W+/g, "_") ) )

    rowContent = ( $("<div/>")
      .attr("class", "row-content") ) 

    projectName = ( $("<div/>")
      .attr("class", "project-name")
      .text(item.name)
      .attr("title", item.name) )

    outerMeterBar = ( $("<div/>")
      .attr("class", "outer-hot-meter-bar") )

    innerMeterBar = $("<div/>")
      .attr("class", "inner-hot-meter-bar")

    # set not to 0%, but to current value
    # innerMeterBar.css("width", "0%")
    # meterBarValue = $("<p/>").text("0%")

    # start at 99% - forces updating
    innerMeterBar.css("width", 99.0 * (item.value - item.minvalue) / (item.maxvalue - item.minvalue) + "%")
    meterBarValue = $("<p/>").text(item.value.toPrecision(3))

    # Put it all together.
    innerMeterBar.append(meterBarValue)
    outerMeterBar.append(innerMeterBar)
    rowContent.append(projectName)
    rowContent.append(outerMeterBar)
    row.append(rowContent)

    return row


  #***/
  # Does calculations for the animation and sets up the javascript
  # interval to perform the animation.
  #
  # @element - element that is going to be animated.
  # @meter_item - an item of the meter_items data received
  # @baseDuration - the minimum time the animation will perform.
  # /
  animateMeterBarContent: (element, item, baseDuration) ->
    from = parseFloat(element.style.width)
    value = parseFloat(item.value)
    maxvalue = parseFloat(item.maxvalue)
    minvalue = parseFloat(item.minvalue)

    # convert to to a percent value
    to = 100.0 * (value - minvalue) / (maxvalue - minvalue)  
    endpointDifference = (to - from)

    if endpointDifference != 0
      currentValue = from

      # Every x milliseconds, the function should run.
      stepInterval = 16.667

      # Change the duration based on the distance between points.
      duration = baseDuration + Math.abs(endpointDifference) * 25

      numberOfSteps = duration / stepInterval
      valueIncrement = endpointDifference / numberOfSteps

      meterBars = this

      interval = setInterval(
        ->
          currentValue += valueIncrement
          if Math.abs(currentValue - from) >= Math.abs(endpointDifference)
            setHotMeterBarValue(element, to, value,
                item.minwarning, item.mincritical,
                item.maxwarning, item.maxcritical,
                item.localScope)
            clearInterval(interval)
          else
            setHotMeterBarValue(element, currentValue,
                    currentValue / 100.0 * ( maxvalue - minvalue) + minvalue,
                item.minwarning, item.mincritical,
                item.maxwarning, item.maxcritical,
                item.localScope)
          updateHotMeterBarStatus(meterBars)
        stepInterval)

      @addInterval(interval)

  #***/
  # Sets the text and width of the element in question to the specified value
  # after making sure it is bounded between [0-100]
  #
  # @element - element to be set
  # @value - the percentage numeric value to set the element to. This can be a float.
  # @text - the text to display
  # @warningThreshold - the treshold at which display a warning visual alert
  # @criticalThreshold - the treshold at which display a critical visual alert
  # @localScope - whether this item can impact the global status of the widget
  # /
  setHotMeterBarValue = (element, value, textvalue,
          minWarningThreshold, minCriticalThreshold,
          maxWarningThreshold, maxCriticalThreshold, localScope) ->
    if (value > 100)
      value = 100
    else if (value < 0)
      value = 0
    element.textContent = textvalue.toPrecision(3)
    element.style.width = value + "%"


    newStatus = switch
      when maxCriticalThreshold and textvalue >= maxCriticalThreshold then 'max-critical'
      when maxWarningThreshold and textvalue >= maxWarningThreshold then 'max-warning'
      when minCriticalThreshold and textvalue <= minCriticalThreshold then 'min-critical'
      when minWarningThreshold and textvalue <= minWarningThreshold then 'min-warning'
      else 'ok'

    for status in ['ok', 'max-critical', 'max-warning',
                     'min-critical', 'min-warning']
      do (status) ->
        match = (newStatus == status)
        $(element).toggleClass("inner-hot-meter-bar-#{status}", match)
        $(element).parent().toggleClass("outer-hot-meter-bar-#{status}", match)

    $(element).toggleClass("global-alert", not localScope)

  #***/
  # Update the widget background accorrding to the meter items status
  #
  # @meterBars - DOM element corresponding to the widget
  # /
  updateHotMeterBarStatus = (meterBars) ->
    meterBars_node = $(meterBars.node)
    overallStatus = switch
      when meterBars_node.find(".inner-hot-meter-bar-critical.global-alert").length then 'critical'
      when meterBars_node.find(".inner-hot-meter-bar-warning.global-alert").length then 'warning'
      else 'ok'

    lastOverallStatus = meterBars.lastOverallStatus
    if lastOverallStatus != overallStatus
      meterBars.lastOverallStatus = overallStatus

      for status in ['ok', 'max-critical', 'max-warning',
            'min-warning', 'min-critical']
        do (status) ->
          meterBars_node.toggleClass("widget-hot-meter-bars-#{status}", overallStatus == status)

      audiosound = meterBars[overallStatus + 'sound']
      audioplayer = new Audio(audiosound) if audiosound?
      if audioplayer
        audioplayer.play()


  #***/
  # Applies a percentage-based row height to the list of rows passed in.
  #
  # @rows - the elements to apply this height value to
  # @percentageOfTotalHeight - The height to be applied to each row.
  # /
  applyCorrectedRowHeight = (rows, percentageOfTotalHeight) ->
    height = percentageOfTotalHeight + "%"
    for row in rows
      row.style.height = height

  #***/
  # Adds a class to every other row to change the background color. This
  # was done mainly for readability.
  #
  # @rows - list of elements to run zebra-striping on
  # /
  applyZebraStriping = (rows) ->
    isZebraStripe = false
    for row in rows
      # In case elements are moved around, we don't want them to retain this.
      row.classList.remove("zebra-stripe")
      if isZebraStripe
        row.classList.add("zebra-stripe")
      isZebraStripe = !isZebraStripe

  #***/
  # Stops all javascript intervals from running and clears the list.
  #/
  clearIntervals: ->
    if @intervalList
      for interval in @intervalList
        clearInterval(interval)
      @intervalList = []

  #***/
  # Adds a javascript interval to a list so that it can be tracked and cleared
  # ahead of time if the need arises.
  #
  # @interval - the javascript interval to add
  #/
  addInterval: (interval) ->
    if !@intervalList
      @intervalList = []
    @intervalList.push(interval)

