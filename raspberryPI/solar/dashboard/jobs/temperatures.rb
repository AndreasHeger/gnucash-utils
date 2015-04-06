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

job_mapping = {
    'TopFloorFrontWall' => ['Temperature.TopFloor.FrontWall', 20, 25],
    'TopFloorFrontCupBoard' => ['Temperature.TopFloor.FrontCupBoard', 20, 25],
    'TopFloorFrontFloor' => ['Temperature.TopFloor.FrontFloor', 20, 25],
    'TopFloorBackFloor' => ['Temperature.TopFloor.BackFloor', 20, 25],
    'TopFloorBackWall' => ['Temperature.TopFloor.BackWall', 20, 25],
    'TopFloorAiringCabinet' => ['Temperature.TopFloor.AiringCabinet', 20, 25],
    'TopFloorAttic' => ['Temperature.TopFloor.Attic', 20, 25],
    'GroundFloorBackDoor' => ['Temperature.GroundFloor.BackDoor', 20, 25],
    'GroundFloorBackWindow' => ['Temperature.GroundFloor.BackWindow', 20, 25],
    'HallwayTop' =>  ['Temperature.Hallway.Top', 20, 25],
    'HallwayBottom' => ['Temperature.Hallway.Bottom', 20, 25],
    'LivingRoomCupBoard' => ['Temperature.LivingRoom.CupBoard', 20, 25],
    'LivingRoomWindow' => ['Temperature.LivingRoom.Window', 20, 25],
    'LandingTop' => ['Temperature.Landing.Top', 20, 25],
    'LandingMiddle' => ['Temperature.Landing.Middle', 20, 25],
    'LandingBottom' => ['Temperature.Landing.Bottom', 20, 25],
    'WaterBoiler' => ['Temperature.Water.Boiler', 20, 25],
    'WaterTank' => ['Temperature.Water.Tank', 20, 25],
}

SCHEDULER.every '30s', :first_in => 0 do |job|

   progress_items = []
   job_mapping.each do |title, dd|
      statname, critical, warning = dd
    
      # create an instance of our Graphite class
      q = Graphite.new GRAPHITE_HOST, GRAPHITE_PORT

      # get the current points and value. Timespan is static set at 1
      # hour.
      value = q.value "#{statname}", "-10min"
      progress_items << {"name" => title,
                         "value" => value,
      "localScope" => TRUE,
      "critical" => critical,
      "warting" => warning}
    end

    send_event("temperatures",
               { "title" => "Temperature",
                 "meter_items" => progress_items })

end
