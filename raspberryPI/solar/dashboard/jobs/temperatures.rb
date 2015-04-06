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
    'TopFloorFrontWall' => ['Temperature.TopFloor.FrontWall', '30s'],
    'TopFloorFrontCupBoard' => ['Temperature.TopFloor.FrontCupBoard', '30s'],
    'TopFloorFrontFloor' => ['Temperature.TopFloor.FrontFloor', '30s'],
    'TopFloorBackFloor' => ['Temperature.TopFloor.BackFloor', '30s'],
    'TopFloorBackWall' => ['Temperature.TopFloor.BackWall', '30s'],
    'TopFloorAiringCabinet' => ['Temperature.TopFloor.AiringCabinet', '30s'],
    'TopFloorAttic' => ['Temperature.TopFloor.Attic', '30s'],
    'GroundFloorBackDoor' => ['Temperature.GroundFloor.BackDoor', '30s'],
    'GroundFloorBackWindow' => ['Temperature.GroundFloor.BackWindow', '30s'],
    'HallwayTop' =>  ['Temperature.Hallway.Top', '30s'],
    'HallwayBottom' => ['Temperature.Hallway.Bottom', '30s'],
    'LivingRoomCupBoard' => ['Temperature.LivingRoom.CupBoard', '30s'],
    'LivingRoomWindow' => ['Temperature.LivingRoom.Window', '30s'],
    'LandingTop' => ['Temperature.Landing.Top', '30s'],
    'LandingMiddle' => ['Temperature.Landing.Middle', '30s'],
    'LandingBottom' => ['Temperature.Landing.Bottom', '30s'],
    'WaterBoiler' => ['Temperature.Water.Boiler', '30s'],
    'WaterTank' => ['Temperature.Water.Tank', '30s'],
}

SCHEDULER.every '30s', :first_in => 0 do |job|

   progress_items = []
   job_mapping.each do |title, dd|
      statname = dd[0]
      interval = dd[1]
    
      # create an instance of our Graphite class
      q = Graphite.new GRAPHITE_HOST, GRAPHITE_PORT

      # get the current points and value. Timespan is static set at 1
      # hour.
      value = q.value "#{statname}", "-10min"
      progress_items << {"name" => title,
                         "value" => value}
    end

    send_event("temperatures",
               { "title" => "Temperature",
                 "meter_items" => progress_items })

end
