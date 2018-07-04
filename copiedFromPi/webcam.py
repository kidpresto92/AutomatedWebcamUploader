import datetime
import ftplib
import math
import os
from picamera import PiCamera
from shutil import copyfile
import subprocess
from time import sleep

#Gloabl Variables

CIVIL_ZENITH = 90.83333 # civil

camera = PiCamera()
camera.resolution = (2560,1920) #5mp
timelapseFolder = "/home/pi/webcam/timelapse/"
localPicturePath = '/home/pi/picture.jpg'

serverIP = '192.168.0.11'
serverPort = 21
serverUsername = 'test'
serverPassword = 'test'

server = ftplib.FTP();
server.connect(serverIP, serverPort);
server.login(serverUsername,serverPassword);

intervalInSeconds = 30
timingBufferInSeconds = 1800

class SunriseSunset(object):
    """
    This class wraps the computation for sunset and sunrise. It relies on the
    datetime class as input and output.
    """
    def __init__(self, dt, latitude, longitude, localOffset=0, zenith=None):
        self.dt          = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        if latitude < -90 or latitude > 90:
            raise ValueError('Invalid latitude value')
        if longitude < -180 or longitude > 180:
            raise ValueError('Invalid longitude value')
        if localOffset < -12 or localOffset > 14:
            raise ValueError('Invalid localOffset value')
        self.latitude    = latitude
        self.longitude   = longitude
        self.localOffset = localOffset
        self.zenith      = zenith if zenith is not None else CIVIL_ZENITH

    # ALGORITHM

    def calculate(self, date=None):
        """Computes the sunset and sunrise for the current day, in local time"""
        if date is None:
            date = self.dt

        # Calculate the day of the year
        N = self.dt.timetuple().tm_yday

        # Convert the longitude to hour value and calculate an approximate time
        lngHour = self.longitude / 15
        t_rise = N + ((6 - lngHour) / 24)
        t_set = N + ((18 - lngHour) / 24)

        # Calculate the Sun's mean anomaly
        M_rise = (0.9856 * t_rise) - 3.289
        M_set = (0.9856 * t_set) - 3.289

        # Calculate the Sun's true longitude, and adjust angle to be between 0
        # and 360
        L_rise = (M_rise + (1.916 * math.sin(math.radians(M_rise))) + (0.020 * math.sin(math.radians(2 * M_rise))) + 282.634) % 360
        L_set = (M_set + (1.916 * math.sin(math.radians(M_set))) + (0.020 * math.sin(math.radians(2 * M_set))) + 282.634) % 360

        # Calculate the Sun's right ascension, and adjust angle to be between 0 and
        # 360
        RA_rise = (math.degrees(math.atan(0.91764 * math.tan(math.radians(L_rise))))) % 360
        RA_set = (math.degrees(math.atan(0.91764 * math.tan(math.radians(L_set))))) % 360

        # Right ascension value needs to be in the same quadrant as L
        Lquadrant_rise  = (math.floor(L_rise/90)) * 90
        RAquadrant_rise = (math.floor(RA_rise/90)) * 90
        RA_rise = RA_rise + (Lquadrant_rise - RAquadrant_rise)

        Lquadrant_set  = (math.floor(L_set/90)) * 90
        RAquadrant_set = (math.floor(RA_set/90)) * 90
        RA_set = RA_set + (Lquadrant_set - RAquadrant_set)

        # Right ascension value needs to be converted into hours
        RA_rise = RA_rise / 15
        RA_set = RA_set / 15

        # Calculate the Sun's declination
        sinDec_rise = 0.39782 * math.sin(math.radians(L_rise))
        cosDec_rise = math.cos(math.asin(sinDec_rise))

        sinDec_set = 0.39782 * math.sin(math.radians(L_set))
        cosDec_set = math.cos(math.asin(sinDec_set))

        # Calculate the Sun's local hour angle
        cos_zenith = math.cos(math.radians(self.zenith))
        radian_lat = math.radians(self.latitude)
        sin_latitude = math.sin(radian_lat)
        cos_latitude = math.cos(radian_lat)
        cosH_rise = (cos_zenith - (sinDec_rise * sin_latitude)) / (cosDec_rise * cos_latitude)
        cosH_set = (cos_zenith - (sinDec_set * sin_latitude)) / (cosDec_set * cos_latitude)

        # Finish calculating H and convert into hours
        H_rise = (360 - math.degrees(math.acos(cosH_rise))) / 15
        H_set = math.degrees(math.acos(cosH_set)) / 15

        # Calculate local mean time of rising/setting
        T_rise = H_rise + RA_rise - (0.06571 * t_rise) - 6.622
        T_set = H_set + RA_set - (0.06571 * t_set) - 6.622

        # Adjust back to UTC, and keep the time between 0 and 24
        UT_rise = (T_rise - lngHour) % 24
        UT_set = (T_set - lngHour) % 24

        # Convert UT value to local time zone of latitude/longitude
        localT_rise = (UT_rise + self.localOffset) % 24
        localT_set = (UT_set + self.localOffset) % 24

        # Conversion
        h_rise = int(localT_rise)
        m_rise = int(localT_rise % 1 * 60)
        h_set = int(localT_set)
        m_set = int(localT_set % 1 * 60)

        # Create datetime objects with same date, but with hour and minute
        # specified
        rise_dt = date.replace(hour=h_rise, minute=m_rise)
        set_dt = date.replace(hour=h_set, minute=m_set)
        return rise_dt, set_dt



def scheduleNextCapture():
    now = datetime.datetime.now()
    rise_obj = SunriseSunset(dt=now,
                            latitude=42.880230,
                            longitude=-78.878738, 
                            localOffset=-5,
                            zenith=CIVIL_ZENITH)
    sunrise, sunset = rise_obj.calculate()

    sunrise = sunrise + datetime.timedelta(0, -timingBufferInSeconds)
    sunset = sunset + datetime.timedelta(0, timingBufferInSeconds)

    # Before sunset, schedule to start before today's sunrise
    if(now < sunrise):  
        nextCapture = now + datetime.timedelta(0, intervalInSeconds)
        scheduleCapture(nextCapture)
    # After sunset, schedule to start before tomorrow's sunrise
    elif(now > sunset):
        tomrorow = now + datetime.timedelta(1)
        rise_obj = SunriseSunset(dt=tomrorow,
                            latitude=42.880230,
                            longitude=-78.878738, 
                            localOffset=-5,
                            zenith=CIVIL_ZENITH)

        nextCapture = getTomorrowsCaptureStart()
        scheduleCapture(nextCapture)

    # Daylight time, take a picture after the desired interval
    else:
        nextCapture = now + datetime.timedelta(0, intervalInSeconds)
        scheduleCapture(nextCapture)

def takePicture():
    camera.start_preview()
    sleep(5)
    camera.capture(localPicturePath)
    camera.stop_preview()

def sendPicture():
    photo = open(localPicturePath, 'rb')
    server.connect(serverIP, serverPort)
    server.login(serverUsername, serverPassword)
    server.storbinary('STOR image.jpg', photo)
    photo.close()
    server.quit()

def getTomorrowsCaptureStart():
    tomorrow =  now = datetime.datetime.now() + datetime.timedelta(1)

    rise_obj = SunriseSunset(dt=tomorrow,
                        latitude=42.880230,
                        longitude=-78.878738, 
                        localOffset=-5,
                        zenith=CIVIL_ZENITH)

    sunrise, sunset = rise_obj.calculate()
    return sunrise + datetime.timedelta(0, -timingBufferInSeconds)

def getFolderName(date):
    directory = timelapseFolder + date.strftime("%Y%m%d") + "/"
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def getTimelapsePhotoName(date):
    folder = getFolderName(date)
    path, dirs, files = next(os.walk(folder))
    
    return folder + "pic-" + "%04d" % (len(files)) + ".jpg"

def getTimelapseFileName(date):
    folder = getFolderName(date)
    path, dirs, files = next(os.walk(folder))
    
    return folder + "timelapse.mp4"

def createTimeLapseVideo(date):
    outputFile =  getTimelapseFileName(date)

    if(not os.path.isfile(outputFile)):

        photoFormat = getFolderName(date) + "pic-%04d.jpg"

        command = "ffmpeg -i " + photoFormat + " " + outputFile
        
        os.system(command)


def copyPictureToTimelapse():
    filename = getTimelapsePhotoName(datetime.datetime.now())
    copyfile(localPicturePath, filename)

def scheduleCapture(date):
    print("Next capture scheduled for " + date.strftime("%Y-%m-%d %H:%M"))
    delay = (date - datetime.datetime.now()).total_seconds()
    sleep(delay)
    execute();

def execute():
    now = datetime.datetime.now()
    rise_obj = SunriseSunset(dt=now,
                            latitude=42.880230,
                            longitude=-78.878738, 
                            localOffset=-5,
                            zenith=CIVIL_ZENITH)
    sunrise, sunset = rise_obj.calculate()

    sunrise = sunrise + datetime.timedelta(0, -timingBufferInSeconds)
    sunset = sunset + datetime.timedelta(0, timingBufferInSeconds)

    print("scheduleNextCapture:now-" + now.strftime("%Y-%m-%d %H:%M"))
    print("scheduleNextCapture:sunrise-" + sunrise.strftime("%Y-%m-%d %H:%M"))
    print("scheduleNextCapture:sunset-" + sunset.strftime("%Y-%m-%d %H:%M"))


    if(sunrise < now and now < sunset):
        takePicture()

        sendPicture()

        copyPictureToTimelapse()

    # elif(sunset < now):
    #     createTimeLapseVideo(now);

    # elif(now < sunset):
    #     yesterday = now.timedelta(-1)
    #     createTimeLapseVideo(yesterday)
    
    scheduleNextCapture()

#For testing purposes only:
# for x in range(100):

#     takePicture()

#     sendPicture()

#     copyPictureToTimelapse()

execute();