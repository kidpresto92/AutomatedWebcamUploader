Automated Webcam Uploader
=========================

##### Designed for the Raspberry Pi Zero W, takes pictures preiodically and uploads them via FTP. This will start firing shortly before the sunrise and stop firing shortly after the sunset based on your latitude, longitude and timezone.

## Componets Needed

Any Raspberry Pi with wifi should work. But I used [this bundle](https://www.amazon.com/gp/product/B0748MPQT4/ref=oh_aui_detailpage_o05_s00?ie=UTF8&psc=1) from Amazon. Also any camera should work, either USB or one like the one I used [this one](https://www.amazon.com/gp/product/B0748MPQT4/ref=oh_aui_detailpage_o05_s00?ie=UTF8&psc=1)

## Setup

#### 1. Download [RASPBIAN STRETCH LITE](https://www.raspberrypi.org/downloads/raspbian/)

#### 2. Flash your micro SD.
Create Boot Drive on your micro SD card with your preferred flasher. I used [Etcher](https://etcher.io/). Once your micro SD card has been flashed, remove it from your computer and plug it back in so your computer will recognize it.

#### 3. Enable SSH 
Open up the drive that you created and add a file in the root of the boot drive named **SSH**. This will enable SSH into your Raspberry Pi since the latest builds do not enable SSH by default.

#### 4. Configure Wifi
Since we're using a headless unit and will be doing most of the work on another computer, you'll need to add your wifi network to the device so it can connect automatically. To do this, Create a file in the root of the boot drive called **wpa_supplicant.conf**. This is commonly used by Linux devices. Here's a template of what to include in the wpa_supplicant.conf file. Once those two files in the boot drive, you can try it out in your raspberry pi zero w.

	```
	country=US
	ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
	update_config=1

	network={
		priority=1
		ssid="preferred wifi's SSID"
		psk="preferred wifi's password"
		key_mgmt=WPA-PSK
	}

	network={
		priority=2
		ssid="secondary wifi's SSID"
		psk="secondary wifi's password"
		key_mgmt=WPA-PSK
	}
	```

#### 5. Wifi Config Check
Once the Raspberry Pi boots you should check to confirm that it connected to your network. I used [Angry IP Scanner](https://angryip.org/) for this.

#### 6. SSH
Open [Putty](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html) and attempt to connect to the raspberry Pi via SSH with the IP address found from Angry IP Scanner. SSH uses port #22 by default.

#### 7. PSCP & quick setup
Another tool that I like to use is PSCP (Also found on the [Putty](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html) site). PSCP is a secure copy scripting tool used in [copyFromPi](copyFromPi) and [copyToPi](copyToPi). These scripts were mostly used for development purposes because it was easier to make code changes on my windows development machine and push the changes over rather than making coding changes in SSH on the Raspberry Pi. So in order to jumpstart the setup, edit [copyToPi](copyToPi) to include the proper IP address and username and password (if you changed them already) then push the files over to the Raspberry Pi.

#### 8. Python Setup
Install pip on your raspberry pi. Through putty, run the commands:
	 ```
	sudo apt-get update
	sudo apt-get install python-pip
	 ```
	If you've copied over the **requirements.txt** file, you can run  
	```
	pip install -r requirements.txt
	```
	Otherwise, you'll have to install the packages listed in the file individually.

#### 9. Enable Camera
You'll need to enable the camera before testing it out. Again with SSH on the Raspberry Pi, run:
	```
	sudo raspi-config
	```
	
	1. Select **Interfacing Options**,
	2. Select **Camera**, 
	3. Then **Yes** for enabling the camera
	4. Select **Exit** to finish

	This Requires a reboot but will initialize the camera when it boots. 

#### 10. Camera Test
After rebooting, try to run [camera_test.py](copiedFromPi\camera_test.py) to confirm that your Raspberry Pi's camera is functioning. If it creates the **picture.jpg** file then the camera is working as expected.

#### 11. FTP Testing
The last part of the app is sending the photo via ftp. In order to test this, I installed [FileZilla Server](https://filezilla-project.org/). I ran FileZilla on 127.0.0.1 so that it could be accessed from the lan. **One important note:** Windows will not allow ftp by default. In order to accept the connection, I had to disable window's firewall. 

#### 12 Running
If you want to run the python process in the background then run it using 
```
sh run.sh
```
and kill it using
```
sh stop.sh
```
Otherwise, you can simply run it on the terminal's process with 
```
python webcam.py
```

#### 13. Auto Start
Since the script will now be run by root, we need to make sure that root has access to the python packages. So install telepot for this
```
sudo pip install telepot
```
Modify /etc/rc.local before the **exit 0** to run the python script with telepot
```
sudo -H -u pi /usr/bin/python /home/piwebcam.py
```


## Authors

* **Aaron Preston** - *Initial work* - [KidPresto](https://github.com/kidpresto92)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* I would like to give a shout out to the [SunriseSunsetCalculator](https://github.com/jebeaudet/SunriseSunsetCalculator) for providing the sunset/sunrise time functionality


## Python support

This module has only been tested on Python 2.7.13 on Jessie Raspbian