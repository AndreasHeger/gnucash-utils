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
    ['TopFloorFrontWall', 'Temperature.TopFloor.FrontWall', 40, 20, 25],
    ['TopFloorFrontCupBoard', 'Temperature.TopFloor.FrontCupBoard', 40, 20, 25],
    ['TopFloorFrontFloor', 'Temperature.TopFloor.FrontFloor', 40, 20, 25],
    ['TopFloorBackFloor', 'Temperature.TopFloor.BackFloor', 40, 20, 25],
    ['TopFloorBackWall', 'Temperature.TopFloor.BackWall', 40, 20, 25],
    ['TopFloorAiringCabinet', 'Temperature.TopFloor.AiringCabinet', 40, 20, 25],
    ['TopFloorAttic', 'Temperature.TopFloor.Attic', 40, 20, 25],
    ['GroundFloorBackDoor', 'Temperature.GroundFloor.BackDoor', 40, 20, 25],
    ['GroundFloorBackWindow', 'Temperature.GroundFloor.BackWindow', 40, 20, 25],
    ['HallwayTop', 'Temperature.Hallway.Top', 40, 20, 25],
    ['HallwayBottom', 'Temperature.Hallway.Bottom', 40, 20, 25],
    ['LivingRoomCupBoard', 'Temperature.LivingRoom.CupBoard', 40, 20, 25],
    ['LivingRoomWindow', 'Temperature.LivingRoom.Window', 40, 20, 25],
    ['LandingTop', 'Temperature.Landing.Top', 40, 20, 25],
    ['LandingMiddle', 'Temperature.Landing.Middle', 40, 20, 25],
    ['LandingBottom', 'Temperature.Landing.Bottom', 40, 20, 25],
    ['WaterBoiler', 'Temperature.Water.Boiler', 60, 50, 55],
    ['WaterTank', 'Temperature.Water.Tank', 60, 50, 55],
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
