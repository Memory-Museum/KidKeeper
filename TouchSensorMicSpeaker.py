# Contributors: Script created by Milan and JC during the Spring of 2024. Modified by Belen in the Fall of 2024. 
# PI: Dr. Jasmine Jones 

## Resources: 
# Send email tutorial: https://www.youtube.com/watch?v=ueqZ7RL8zxM


import RPi.GPIO as GPIO
import subprocess
import os
import time
from datetime import datetime

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import date 
from dotenv import load_dotenv
import os

# Setup your capacitive touch sensor pin
touchSensorPin = 21
audio_folder = "./TouchSensor/audios/" # we are saving the recorded audios in a diferent directory to keep that secured.
smtp_port = 587                 # Standard secure SMTP port
smtp_server = "smtp.gmail.com"  # Google SMTP Server 

# Set up the email lists
email_from = "marb5786@gmail.com"
email_list = ["belensaavedra.bo@gmail.com"]

# call token 
load_dotenv()
pswd = os.getenv("pswd") 

def setup():
    '''
    setup function that runs all the necessary variables  
    '''
    GPIO.setmode(GPIO.BCM)  # Use BCM numbering
    GPIO.setup(touchSensorPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Setup touch sensor pin
    if not os.path.exists(audio_folder):
        os.makedirs(audio_folder)

def record_audio(filename, duration=10):
    """
    Record audio 
    args: 
    filename:  string 
    duration: int 

    """
    full_path = f"{filename}.wav"
    command = f"arecord -d {duration} -f S16_LE -q {full_path}"
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"Error: Audio recording failed with return code {result.returncode}")
    else:
        print(f"Audio recorded successfully: {full_path}")


def play_audio(filename, volume_percent=100) -> None:
    '''
    Plays wav audio files
    args: 
    filename: string
    volume_percent: int 
    '''
    full_path = f"{filename}.wav"

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Audio file {full_path} not found for playback.")

    # Adjust the system volume
    set_volume_command = f"amixer set Master {volume_percent}%"
    subprocess.run(set_volume_command, shell=True)
    # Command to play audio file
    play_command = f"aplay {full_path}"
    subprocess.run(play_command, shell=True)


def send_emails(email_list) -> None:
    '''
    Structure email text, select the most recently recorded video and send emai. 

    args: 
    email_list: list of emails to send the audio, this is set in a global function
    
    '''
    today = date.today()
    subject = f"KidKeeper: An Update from {today}"
    audio_path = '/home/milangarciaj/Documents/TouchSensor/audios'

    for person in email_list:
        body = """
        
        Dear Kid Keeper user, 
        
        Were you wondering what has your kid been up to? We have a new memory for you. 

        Best,

        The KidKeeper development team
        """

        # make a MIME object to define parts of the email
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = person
        msg['Subject'] = subject

        # Attach the body of the message
        msg.attach(MIMEText(body, 'plain'))

        # get a list of all audio recordings sorted by creation time (newest first)
        audio_files = sorted(
            [f for f in os.listdir(audio_path) if f.endswith(".wav")],
            key=lambda x: os.path.getctime(os.path.join(audio_path, x)),
            reverse=True
        )

        # Ensure there is at least one audio file to send
        if not audio_files:
            print("No audio files found.")
            return

        # Select the most recent file
        most_recent_audio = audio_files[0]
        full_path = os.path.join(audio_path, most_recent_audio)

        # Open the most recent file as binary
        with open(full_path, 'rb') as attachment:
            attachment_package = MIMEBase('application', 'octet-stream')
            attachment_package.set_payload(attachment.read())
            encoders.encode_base64(attachment_package)
            attachment_package.add_header('Content-Disposition', f"attachment; filename={most_recent_audio}")
            msg.attach(attachment_package)

        # Send the email
        text = msg.as_string()
        print("Connecting to server...")
        with smtplib.SMTP(smtp_server, smtp_port) as TIE_server:
            TIE_server.starttls()
            TIE_server.login(email_from, pswd)
            print("Successfully connected to server")
            print(f"Sending email to: {person}...")
            TIE_server.sendmail(email_from, person, text)
            print(f"Email sent to: {person}")



def loop():
    """
    Function that runs all the logic of the program

    args: None
    """
    print("System ready. Touch the sensor to record and play audio.")
    isSensorTouched = False
    
    while True:
        if GPIO.input(touchSensorPin) == GPIO.HIGH:
            print("Touched sensor")
            # add feedback sound
            play_audio("/home/milangarciaj/Documents/KidKeeper/feedback_sound")
            isSensorTouched = True
            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Get current date and time
            audio_file = os.path.join(audio_folder, f"recorded_audio_{current_time}")
            print("Touch detected! Recording and playing back audio...")
            record_audio(audio_file)
            play_audio(audio_file)
            #delay here

        elif GPIO.input(touchSensorPin) == GPIO.LOW and isSensorTouched:
            isSensorTouched = False
            print("Sensor released, sending email...")
            send_emails(email_list)
            

if __name__ == '__main__':
    setup()
    try:
        loop()

    except KeyboardInterrupt:
        print("Exiting program")
        GPIO.cleanup()  
