require 'net/http'
require 'json'
require 'date'

# Job mappings. Define a name and set the metrics name from graphite

job_mapping = [
    { "title" => 'Fabian',
      "stat" => 'Temperature.TopFloor.FrontWall',
      "breakpoints" => [0,10,15,22,25,40],
               },
    { "title" => 'Niamh',
      "stat" => 'Temperature.TopFloor.BackWall',
      "breakpoints" => [0,10,15,22,25,40],
               },
    { "title" => 'Keeva',
      "stat" => 'Temperature.TopFloor.BackFloor',
      "breakpoints" => [0,10,15,22,25,40],
               },
    { "title" => 'Living room',
      "stat" => 'Temperature.LivingRoom.Window',
      "breakpoints" => [0,10,15,22,25,40],
               },
    { "title" => 'Garden room',
      "stat" => 'Temperature.GroundFloor.BackWindow',
      "breakpoints" => [0,10,15,22,25,40],
               },
    { "title" => 'Airing cabinet',
      "stat" => 'Temperature.TopFloor.AiringCabinet',
      "breakpoints" => [0,10,15,35,40,50],
               },
    { "title" => 'Attic',
      "stat" => 'Temperature.TopFloor.Attic',
      "breakpoints" => [0,5,10,30,40,50],
               },
    { "stat" => 'Temperature.TopFloor.FrontCupBoard',
      "breakpoints" => [0,10,15,22,25,40],
               },
    { "stat" => 'Temperature.TopFloor.FrontFloor',
      "breakpoints" => [0,10,15,22,25,40],
               },
    { "stat" => 'Temperature.GroundFloor.BackDoor',
      "breakpoints" => [0,10,15,22,25,40],
               },
    { "stat" => 'Temperature.Hallway.Top',
      "breakpoints" => [0,10,15,22,25,40],
               },
    { "stat" => 'Temperature.Hallway.Bottom',
      "breakpoints" => [0,10,15,22,25,40],
               },
    { "stat" => 'Temperature.LivingRoom.CupBoard',
      "breakpoints" => [0,10,15,22,25,40],
               },
    { "stat" => 'Temperature.Landing.Top',
      "breakpoints" => [0,10,15,22,25,40],
               },
    { "stat" => 'Temperature.Landing.Middle',
      "breakpoints" => [0,10,15,22,25,40],
               },
    { "stat" => 'Temperature.Landing.Bottom',
      "breakpoints" => [0,10,15,22,25,40],
               },
    { "stat" => 'Temperature.Water.Boiler',
      "breakpoints" => [0,10,20,40,58,60],
               },
    { "stat" => 'Temperature.Water.Tank',
      "breakpoints" => [0,35,40,55,58,60],
               },
]

SCHEDULER.every '30s', :first_in => 0 do |job|

   progress_items = []
   job_mapping.each do |item|

      # create an instance of our Graphite class
      q = Graphite.new GRAPHITE_HOST, GRAPHITE_PORT
      stat = item["stat"]
      minvalue, mincritical, minwarning, maxwarning, maxcritical, maxvalue = item["breakpoints"]
      # get the current points and value. Timespan is static set at 1
      # hour.
      value = q.value "#{stat}", "-10min"
      progress_items << {
      "name" => item.has_key?("title") ? item["title"] : stat,
      "value" => value,
      "localScope" => TRUE,
      "maxvalue" => maxvalue,
      "minvalue" => minvalue,
      "maxwarning" => maxwarning,
      "maxcritical" => maxcritical,
      "minwarning" => minwarning,
      "mincritical" => mincritical}
    end

    send_event("temperatures",
               { "title" => "Temperature",
                 "meter_items" => progress_items })

end
