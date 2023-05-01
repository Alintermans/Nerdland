# Nerdland - Eye Controlled RC-Cars
For the stand of the KU Leuven at the Nerdland Festival this project was made in order to steer little RC cars with the movements of the eyes by connecting two electrodes to the head of the user. 4 RC cars are able to be simultaneosly be used by the setup. 

## Setup of the project
- Raspberry Pi
- One computer
- Ethernet Cable
- 4 ADC + necessary cables (and resistors)
- 8 elektrodes (2 per ADC)
- 4 RC Cars
- 4 modified controllers for which the left and right buttons (and ground) are wired up, to be connected to the raspberry pi (only possible if the voltage on the buttons is also ±3.3v which is the output voltage of the GPIO pins from the Raspberry pi)

The Raspberry pi hosts the sever on which everything runs to controll the RC Cars. The 4 ADC's which are connected to the raspberry pi as well as all cables connecting the controllers to the GPIO pins of the  Raspberry Pi. The PI also hosts a web application on which everything can be controlled. The Pi is connected via an ethernet cable to a secondary computer to show the web interface on. 

## Getting Started
First make sure all requirements are met and all cables are plugged into the right place. 

Then go to terminal connect to raspberry pi via ssh (i.e. ssh pi@raspberry.local with the password: Raspberry). You can start the web application by first going to ~/Desktop/Nerdland and starting the webapplication by calling the command $sudo python3 main.py.

Afterwards you can connect to the webappication by going to the web browser and opening the raspberry.local website. When you're connected, you can start using the whole setup and start controlling the car by pressing on the Start button and waiting for it to be calibrated to use it correctly. 


## Requirements 
### Raspberry pi 
You need to have installed the python package PyUSB (make sure to use SUDO when installing, to install it in the admin env.) and also use ... to setup a local dns so the raspberry pi can easily be accesed by the domain raspberry.local

### Connected Computer
The only thing you need is to be able to run a web browser (which all computers can) and it needs to have an ethernet port. To be able to reach the raspberry pi over the ethernet cable you need to setup a local network on the computer as follows:

#### Mac OS

1. Go to settings -> Sharing -> InternetSharing 
2. set "Share the connection Throuh" to 'Wifi'
3. Set "With the computers that use" and select the dongle that has the ethernet connection (the correct dongle can be found by going to Settings -> Network -> and looking at the one that has a green dot apart from Wifi)

Now your mac can talk to Raspberry Pi. 

#### Windows

#### Linux




## Structure of the application
So all the code of the flask web apllication is located in the main.py file together with al the code for the sampling, it also hosts all settings that can be adpated. 
The html page is located in the templates folder. All assets, styling and JS code are located in the static folder. 


## Author
Anton Lintermans


