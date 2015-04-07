require 'net/http'
require 'json'
require 'date'

# Pull data from Graphite and make available to Dashing Widgets
# Heavily inspired from Thomas Van Machelen's "Bling dashboard article"

# Set the graphite host and port (ip or hostname)
GRAPHITE_HOST = '192.168.0.61'
GRAPHITE_PORT = '8080'
INTERVAL = '30s'

# Job mappings. Define a name and set the metrics name from graphite

job_mapping = [
    ['Fabian', 'Temperature.TopFloor.FrontWall', 40, 22, 25],
    ['Niamh', 'Temperature.TopFloor.BackWall', 40, 22, 25],
    ['Keeva', 'Temperature.TopFloor.BackFloor', 40, 22, 25],
    ['Airing cabinet', 'Temperature.TopFloor.AiringCabinet', 50, 30, 40],
    ['Attic', 'Temperature.TopFloor.Attic', 50, 40, 45],
    ['Living room', 'Temperature.LivingRoom.Window', 40, 22, 25],
    ['Garden room', 'Temperature.GroundFloor.BackWindow', 40, 22, 25],
    ['TopFloorFrontCupBoard', 'Temperature.TopFloor.FrontCupBoard', 40, 22, 25],
    ['TopFloorFrontFloor', 'Temperature.TopFloor.FrontFloor', 40, 22, 25],

    ['GroundFloorBackDoor', 'Temperature.GroundFloor.BackDoor', 40, 22, 25],
    ['HallwayTop', 'Temperature.Hallway.Top', 40, 22, 25],
    ['HallwayBottom', 'Temperature.Hallway.Bottom', 40, 22, 25],
    ['LivingRoomCupBoard', 'Temperature.LivingRoom.CupBoard', 40, 22, 25],
    ['LandingTop', 'Temperature.Landing.Top', 40, 22, 25],
    ['LandingMiddle', 'Temperature.Landing.Middle', 40, 22, 25],
    ['LandingBottom', 'Temperature.Landing.Bottom', 40, 22, 25],
    ['WaterBoiler', 'Temperature.Water.Boiler', 60, 45, 55],
    ['WaterTank', 'Temperature.Water.Tank', 60, 45, 55],
]

SCHEDULER.every '30s', :first_in => 0 do |job|

   progress_items = []
   job_mapping.each do |item|
      title, statname, maxvalue, warning, critical = item
    
      # create an instance of our Graphite class
      q = Graphite.new GRAPHITE_HOST, GRAPHITE_PORT

      # get the current points and value. Timespan is static set at 1
      # hour.
      value = q.value "#{statname}", "-10min"
      progress_items << {
      "name" => title,
      "value" => value,
      "localScope" => TRUE,
      "maxvalue" => maxvalue,
      "critical" => critical,
      "warting" => warning}
    end

    send_event("temperatures",
               { "title" => "Temperature",
                 "meter_items" => progress_items })

end
