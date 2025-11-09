We built this small HackUMass project that serves as a fun addition to a gaming experience. The project is called Rage Meter, a project that tracks the facial expressions of two users, analyzes their emotion, and follows up with quippy comments based on the user's mood. This project uses the Raspberry Pi 5 as it's hardware, and uses libraries like OpenCV, Deepface, NumPy, and Picamera2 to integrate.  

QUICK START (Raspberry Pi5)

# open terminal and clone our repo
mkdir <folder-name>
git clone https://github.com/aamirelhaissouni/Hackathon-2026-Chuds.git
cd Hackathon-2026-Chuds

# create pyenv virtual environment
python -m venv .venv
source venv/bin/activate
pip install -r requirements.txt

# set up breadboard (list of needed pieces and picture of set-up)
- raspberry pi 5 & power supply
- raspberry pi camera module 3
- breadboard
- jumper wires
- 1000 nanoFarad capacitor
- 220 microFarad capacitor
- 1 microFarad transistor
- LM386 amplifier 
![newimage](https://github.com/user-attachments/assets/11a7dd36-7ee5-417b-a4f1-a70362db244e)


# make sure you are in src, run script
~/home/pi/<foldername>/Hackathon-2026-Chuds/src
run python3 main.py


Feel Free to Contribute!
