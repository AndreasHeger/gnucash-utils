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
   {"name" => "energy",
    "interval" => "5s",
    "since" => "-10hour",
    "metrics" => ['Wattson.Power.Grid',
                  'Wattson.Power.Solar']
               },
   {"name" => "solarpower",
    "interval" => "5s",
    "since" => "-10hour",
    "metrics" => ['Solar.Power.East',
                  'Solar.Power.West',
                  'Solar.Power.Total']
               }
]


# Extend the float to allow better rounding. Too many digits makes a messy dashboard
class Float
    def sigfig_to_s(digits)
        f = sprintf("%.#{digits - 1}e", self).to_f
        i = f.to_i
        (i == f ? i : f)
    end
end

# class Graphite
#     # Initialize the class
#     def initialize(host, port)
#         @host = host
#         @port = port
#     end

#     # Use Graphite api to query for the stats, parse the returned JSON
#     # and return the result
#     def query(statname, since=nil)
#         since ||= '-1hour'
#         http = Net::HTTP.new(@host, @port)
#         response = http.request(Net::HTTP::Get.new("/render?format=json&target=#{statname}&from=#{since}"))
#         result = JSON.parse(response.body, :symbolize_names => true)
#         return result.first
#     end

#     # Gather the datapoints and turn into Dashing graph widget format
#     def points(name, since=nil)
#         since ||= '-1min'
#         stats = query(name, since)
#         datapoints = stats[:datapoints]
#         points = []
#         count = 1
#         (datapoints.select { |el| not el[0].nil? }).each do|item|
#             points << {x: item[1], y: item[0] || 0}
#             count += 1
#         end

#         return points
#     end

# end

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

