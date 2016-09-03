import sys, math
import dronekit_sitl
from dronekit import connect, VehicleMode, time, LocationGlobalRelative, mavutil


# append python module path for opencv and numpy
sys.path.append("/usr/lib/python2.7/site-packages")

sitl = dronekit_sitl.start_default()
connection_string = sitl.connection_string()

# Connect to UDP endpoint (and wait for default attributes to accumulate)
vehicle = connect(connection_string, wait_ready=True)
takeoff_location = vehicle.location.global_frame
print "GPS Coordinates (lat/lon): " + str(takeoff_location.lat) + ", " + str(takeoff_location.lon)
print "Battery: " + str(vehicle.battery)

# Camera resolution
horizontal_resolution = 1280
vertical_resolution = 720

# Camera FOV (radians) - References:
# https://gopro.com/support/articles/hero3-field-of-view-fov-information
# https://gopro.com/support/articles/video-resolution-settings-and-format
horizontal_fov = math.radians(118.2)
vertical_fov = math.radians(69.5)

def arm_and_takeoff(aTargetAltitude):
    """
    Arms vehicle and fly to aTargetAltitude.
    """
    print "Basic pre-arm checks"
    # Don't try to arm until autopilot is ready
    while not vehicle.is_armable:
        print " Waiting for vehicle to initialise..."
        time.sleep(1)

    print "Arming motors"
    # Copter should arm in GUIDED mode
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    # Confirm vehicle armed before attempting to take off
    while not vehicle.armed:
        print " Waiting for arming..."
        time.sleep(1)

    print "Taking off!"
    vehicle.simple_takeoff(aTargetAltitude) # Take off to target altitude NOTE: asynchronous method

    # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command
    #  after Vehicle.simple_takeoff will execute immediately).
    while True:
        print " Altitude: ", vehicle.location.global_relative_frame.alt
        #Break and return from function just below target altitude.
        if vehicle.location.global_relative_frame.alt>=aTargetAltitude*0.95:
            print "Reached target altitude"
            break
        time.sleep(1)


def send_ned_velocity(velocity_x, velocity_y, velocity_z, duration):
    # Set up velocity mappings
    # velocity_x > 0 => fly North
    # velocity_x < 0 => fly South
    # velocity_y > 0 => fly East
    # velocity_y < 0 => fly West
    # velocity_z < 0 => ascend
    # velocity_z > 0 => descend

    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_FRAME_LOCAL_NED, # frame
        0b0000111111000111, # type_mask (only speeds enabled)
        0, 0, 0, # x, y, z positions (not used)
        velocity_x, velocity_y, velocity_z, # x, y, z velocity in m/s
        0, 0, 0, # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

    # send command to vehicle on 1 Hz cycle
    for x in range(0,duration):
        vehicle.send_mavlink(msg)
        time.sleep(1)


def condition_yaw(heading, relative=False):
    """
    Send MAV_CMD_CONDITION_YAW message to point vehicle at a specified heading (in degrees).
    This method sets an absolute heading by default, but you can set the `relative` parameter
    to `True` to set yaw relative to the current yaw heading.
    By default the yaw of the vehicle will follow the direction of travel. After setting
    the yaw using this function there is no way to return to the default yaw "follow direction
    of travel" behaviour (https://github.com/diydrones/ardupilot/issues/2427)
    For more information see:
    http://copter.ardupilot.com/wiki/common-mavlink-mission-command-messages-mav_cmd/#mav_cmd_condition_yaw
    """
    if relative:
        is_relative = 1 #yaw relative to direction of travel
    else:
        is_relative = 0 #yaw is an absolute angle
    # create the CONDITION_YAW command using command_long_encode()
    msg = vehicle.message_factory.command_long_encode(
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_CMD_CONDITION_YAW, #command
        0, # confirmation
        heading,    # param 1, yaw in degrees
        0,          # param 2, yaw speed deg/s
        1,          # param 3, direction -1 ccw, 1 cw
        is_relative, # param 4, relative offset 1, absolute angle 0
        0, 0, 0)    # param 5 ~ 7 not used
    # send command to vehicle
    vehicle.send_mavlink(msg)


def send_land_message(x, y):
    """ lands the drone at target

    References: http://mavlink.org/messages/common#LANDING_TARGET

    Args:
        x:
        y:

    Returns:

    """
    print "Landing!!"
    msg = vehicle.message_factory.landing_target_encode(
        0,       # time_boot_ms (not used)
        0,       # target num
        0,       # frame
        (x - horizontal_resolution / 2) * horizontal_fov / horizontal_resolution,
        (y - vertical_resolution / 2) * vertical_fov / vertical_resolution,
        0,       # altitude.  Not supported.
        0,0)     # size of target in radians
    vehicle.send_mavlink(msg)
    #vehicle.flush()


arm_and_takeoff(10)
vehicle.airspeed = 3

point1 = LocationGlobalRelative(-35.361354, 149.165218, float(vehicle.location.global_frame.alt)) # change the gps coordinates
vehicle.simple_goto(point1)


send_land_message(0, 0)
print vehicle.location.global_frame.alt

time.sleep(30)
print vehicle.location.global_frame.alt




# Ending Delivery
print("Returning home/landing")
vehicle.mode = VehicleMode("RTL")  # RTL returns home, LAND lands wherever the drone currently is

# Close vehicle object before exiting script
print "Close vehicle object"
vehicle.close()

print("Completed")


# test script shit
def send_land_message(x, y):
    """ lands the drone at target

    References: http://mavlink.org/messages/common#LANDING_TARGET

    Args:
        x:
        y:

    Returns:

    """
    print "Landing!!"
    msg = vehicle.message_factory.landing_target_encode(
        0,       # time_boot_ms (not used)
        0,       # target num
        0,       # frame
        (x - horizontal_resolution / 2) * horizontal_fov / horizontal_resolution,
        (y - vertical_resolution / 2) * vertical_fov / vertical_resolution,
        0,       # altitude.  Not supported.
        0,0)     # size of target in radians
    vehicle.send_mavlink(msg)
    vehicle.flush()


def arm_and_takeoff(aTargetAltitude):
    """
    Arms vehicle and fly to aTargetAltitude.
    """
    print "Basic pre-arm checks"
    # Don't try to arm until autopilot is ready
    while not vehicle.is_armable:
        print " Waiting for vehicle to initialise..."
        time.sleep(1)

    print "Arming motors"
    # Copter should arm in GUIDED mode
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    # Confirm vehicle armed before attempting to take off
    while not vehicle.armed:
        print " Waiting for arming..."
        time.sleep(1)

    print "Taking off!"
    vehicle.simple_takeoff(aTargetAltitude) # Take off to target altitude NOTE: asynchronous method

    # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command
    #  after Vehicle.simple_takeoff will execute immediately).
    while True:
        print " Altitude: ", vehicle.location.global_relative_frame.alt
        #Break and return from function just below target altitude.
        if vehicle.location.global_relative_frame.alt>=aTargetAltitude*0.95:
            print "Reached target altitude"
            break
        time.sleep(1)
