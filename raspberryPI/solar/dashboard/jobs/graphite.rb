require 'net/http'
require 'json'
require 'date'

# Pull data from Graphite and make available to Dashing Widgets
# Heavily inspired from Thomas Van Machelen's "Bling dashboard article"

# Set the graphite host and port (ip or hostname)
GRAPHITE_HOST = '192.168.0.55'
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
    'Hallway Bottom' => ['Temperature.Hallway.Bottom', '30s'],
    'LivingRoomCupBoard' => ['Temperature.LivingRoom.CupBoard', '30s'],
    'LivingRoomWindow' => ['Temperature.LivingRoom.Window', '30s'],
    'LandingTop' => ['Temperature.Landing.Top', '30s'],
    'LandingMiddle' => ['Temperature.Landing.Middle', '30s'],
    'LandingBottom' => ['Temperature.Landing.Bottom', '30s'],
    'WaterBoiler' => ['Temperature.Water.Boiler', '30s'],
    'WaterTank' => ['Temperature.Water.Tank', '30s'],
    'WattsonPowerGrid' => ['Wattson.Power.Grid', '2s'],
    'WattsonPowerSolar' => ['Wattson.Power.Solar', '2s'],
}



# Extend the float to allow better rounding. Too many digits makes a messy dashboard
class Float
    def sigfig_to_s(digits)
        f = sprintf("%.#{digits - 1}e", self).to_f
        i = f.to_i
        (i == f ? i : f)
    end
end

class Graphite
    # Initialize the class
    def initialize(host, port)
        @host = host
        @port = port
    end

    # Use Graphite api to query for the stats, parse the returned JSON and return the result
    def query(statname, since=nil)
        since ||= '1h-ago'
        http = Net::HTTP.new(@host, @port)
        response = http.request(Net::HTTP::Get.new("/render?format=json&target=#{statname}&from=#{since}"))
        result = JSON.parse(response.body, :symbolize_names => true)
        return result.first
    end

    # Gather the datapoints and turn into Dashing graph widget format
    def points(name, since=nil)
        since ||= '-1min'
        stats = query name, since
        datapoints = stats[:datapoints]

        points = []
        count = 1

        (datapoints.select { |el| not el[0].nil? }).each do|item|
            points << { x: count, y: get_value(item)}
            count += 1
        end

        v = (datapoints.select { |el| not el[0].nil? })
        # puts "name=#{name} #{datapoints.length} #{v}"

        # value = (datapoints.select { |el| not el[0].nil? }).last[0].sigfig_to_s(3)
        # puts "name=#{name} #{datapoints.length} #{v} #{value}"
        value = (datapoints.select { |el| not el[0].nil? }).last[0]
        return points, value
    end

    def get_value(datapoint)
        value = datapoint[0] || 0
        return value.round(2)
    end

    def value(name, since=nil)
        since ||= '-10min'
        stats = query name, since
        last = (stats[:datapoints].select { |el| not el[0].nil? }).last[0].sigfig_to_s(2)
        return last
    end
end

job_mapping.each do |title, dd|
  statname = dd[0]
  interval = dd[1]
    
  # dictionary with last values, can this be
  # attached to the job?
  last_values = {}

  SCHEDULER.every interval, :first_in => 0 do |job|
    # create an instance of our Graphite class
    q = Graphite.new GRAPHITE_HOST, GRAPHITE_PORT

    # get the current points and value. Timespan is static set at 1 hour.
    points, current = q.points "#{statname}", "-1hour"

    last_values[title] ||= current

    # send to dashboard, supports for number (current, last), meter (value)
    # and graph widgets (points)
    send_event("#{title}", { 
                 current: current.sigfig_to_s(2),
                 value: current,
                 last: last_values[title],
                 points: points })

    last_values[title] = current
  end
end

# job_mapping.each do |title, statname|
#    SCHEDULER.every INTERVAL, :first_in => 0 do
#         # Create an instance of our Graphite class
#         q = Graphite.new GRAPHITE_HOST, GRAPHITE_PORT

#         # Get the current points and value. Timespan is static atm
#         points, current = q.points "#{statname}", "-1hour"

#         # Send to dashboard, tested supports for number, meter and graph widgets
#         send_event "#{title}", { current: current, value: current, points: points }
#    end
# end
