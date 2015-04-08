require 'net/http'
require 'json'
require 'date'

# Job mappings. Define a name and set the metrics name from graphite
job_mapping = [
   {"name" => "energy",
    "interval" => "5s",
    "since" => "-4hour",
    "metrics" => ['Wattson.Power.Grid',
                  'Wattson.Power.Solar']
               },
   {"name" => "solarpower",
    "interval" => "5s",
    "since" => "-24hour",
    "metrics" => ['Solar.Power.East',
                  'Solar.Power.West',
                  'Solar.Power.Total']
               }
]

job_mapping.each do |entry|

   SCHEDULER.every entry["interval"], :first_in => 0 do |job|

      # create an instance of our Graphite class
      q = Graphite.new(GRAPHITE_HOST, GRAPHITE_PORT)

      series = []
      since = entry["since"]

      entry["metrics"].each do |metric|
        
        _points, current = q.points("#{metric}", since)
        series << { 
          "name"=> metric,
          "data"=> _points }
      end

      send_event(entry["name"], { 
                   series: series })
   end
end

