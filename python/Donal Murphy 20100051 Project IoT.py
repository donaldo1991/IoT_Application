import datetime, BlynkLib, firebase_admin
import os, io, logging, socketserver, requests
#from sense_hat import SenseHat

from firebase_admin import credentials, firestore, storage, db
from time import sleep
from gpiozero import Servo, MotionSensor
from picamera import PiCamera
from threading import Condition, Thread
from http import server

cred=credentials.Certificate('./serviceAccountKey.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': 'smart-pet-monitor-a9aaf.appspot.com',
    'databaseURL': 'https://smart-pet-monitor-a9aaf-default-rtdb.europe-west1.firebasedatabase.app/'
})

bucket = storage.bucket()
ref = db.reference('/')
home_ref = ref.child('file')

servo = Servo(18)
xPir = MotionSensor(27) # x axis
yPir = MotionSensor(10) # y axis
zPir = MotionSensor(22) # z axis

pos = -1
servo.value = pos

#camera = PiCamera()
#camera.start_preview()
image = 1

BLYNK_AUTH = '4vCAOv5DCXvNBBoRPnvvqwL9lM4aSS2s'

#initialize Blynk
blynk = BlynkLib.Blynk(BLYNK_AUTH)

#initialise SenseHAT
#sense = SenseHat()
#sense.clear()

# register handler for virtual pin V0 write event
@blynk.on("V0")
def v3_write_handler(value):
    buttonValue=value[0]
    print(f'Current button value: {buttonValue}')
    if buttonValue=="1":
        servo.value = 1
    else:
        servo.value = -1

def store_file(fileLoc):

    filename=os.path.basename(fileLoc)

    # Store File in FB Bucket
    blob = bucket.blob(filename)
    outfile=fileLoc
    blob.upload_from_filename(outfile)

def push_db(fileLoc, time):

  filename=os.path.basename(fileLoc)

  # Push file reference to image in Realtime DB
  home_ref.push({
      'image': filename,
      'timestamp': time}
  )

def blynk_conn():
# infinite loop that waits for event
  while True:
      print("connection exists")
      sleep(0.5)
      blynk.run()
      #blynk.virtual_write(1, round(sense.temperature,2))
      #blynk.virtual_write(2, round(sense.humidity,2))
      print("PIR x is at value: " + str(xPir.value))
      print("PIR y is at value: " + str(yPir.value))
      print("PIR z is at value: " + str(zPir.value))
      if xPir.value & yPir.value & zPir.value == 1:
        global image
        print("Movement - send image to firebase & start camera stream to Blynk")
        picloc = f'/home/pi/Pictures/assessment2/image{image}.jpg'
        currentTime = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        takeImage(picloc)
        print(f'Image {image} taken at {currentTime}')
        store_file(picloc)
        push_db(picloc, currentTime)
        print('Image stored and location pushed to db')
        #streamCamera(500)
        th.start()
        print('Streaming to Blynk')
        image += 1
        sleep(15)

def takeImage(picloc):
    with PiCamera(resolution='640x480', framerate=24) as camera: 
        camera.capture(picloc)

def streamCamera():
    global server
    duration = 500
    class StreamingOutput(object):
        def __init__(self):
            self.frame = None
            self.buffer = io.BytesIO()
            self.condition = Condition()

        def write(self, buf):
            if buf.startswith(b'\xff\xd8'):
                # New frame, copy the existing buffer's content and notify all
                # clients it's available
                self.buffer.truncate()
                with self.condition:
                    self.frame = self.buffer.getvalue()
                    self.condition.notify_all()
                self.buffer.seek(0)
            return self.buffer.write(buf)

    class StreamingHandler(server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            i = 0
            while i <= duration:
                with output.condition:
                    output.condition.wait()
                    frame = output.frame
                self.wfile.write(b'--FRAME\r\n')
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Content-Length', len(frame))
                self.end_headers()
                self.wfile.write(frame)
                self.wfile.write(b'\r\n')
                i += 1
            return    

    class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
        allow_reuse_address = True
        daemon_threads = True

    with PiCamera(resolution='640x480', framerate=24) as camera:
        output = StreamingOutput()
        camera.start_recording(output, format='mjpeg')
        i = 0
        while i < duration:
            address = ('', 8000)
            server = StreamingServer(address, StreamingHandler)
            server.serve_forever()
            i += 1
        server.server_close()
        camera.stop_recording()
        return

if __name__ == "__main__":
    th = Thread(target=streamCamera)
    blynk_conn()

