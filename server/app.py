from flask import Flask, Response, render_template, request, jsonify, json
from werkzeug.utils import secure_filename
from image_scraper.scraper import scrape_images
from image_scraper.csv_handler import save_to_csv
from detector.deepfake_detector import check_images_for_deepfakes, detectFakeVideo
import webbrowser
import csv
from dotenv import load_dotenv
from flask_sockets import Sockets
import os
import numpy as np
import cv2
from skimage import img_as_ubyte
import warnings



warnings.filterwarnings("ignore")

os.environ['KMP_DUPLICATE_LIB_OK']='True'
load_dotenv()
HOST_URL = os.getenv('HOST_URL')

UPLOAD_FOLDER = 'Uploaded_Files'
video_path = ""

detectOutput = []

app = Flask("__main__", template_folder="templates")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
sockets = Sockets(app)

@app.route('/', methods=['POST', 'GET'])
def homepage():
	return render_template('index.html')




@app.route('/api', methods=['POST'])
def returnpredict():  
  video = request.files['video']
  print(video.filename)
  video_filename = secure_filename(video.filename)
  video.save(os.path.join(app.config['UPLOAD_FOLDER'], video_filename))
  video_path = "Uploaded_Files/" + video_filename
  full_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
  prediction = detectFakeVideo(video_path)
  os.remove(full_path)
  if prediction[0] == 0:
    output = "FAKE"
  else:
    output = "REAL"
  confidence = prediction[1]
  data = {'output': output, 'confidence': confidence}
  data = json.dumps(data)
  #  d={}
  #  inputvideo=str(request.files['query'])
  #  prediction = detectFakeVideo(inputvideo)
  #  d['output'] = prediction
  return data

@app.route('/Detect', methods=['POST', 'GET'])
def DetectPage():
    if request.method == 'GET':
        return render_template('index.html')
    if request.method == 'POST':
        video = request.files['video']
        print(video.filename)
        video_filename = secure_filename(video.filename)
        video.save(os.path.join(app.config['UPLOAD_FOLDER'], video_filename))
        video_path = "Uploaded_Files/" + video_filename
        prediction = detectFakeVideo(video_path)
        print(prediction)
        if prediction[0] == 0:
              output = "FAKE"
        else:
              output = "REAL"
        confidence = prediction[1]
        data = {'output': output, 'confidence': confidence}
        data = json.dumps(data)
        os.remove(video_path)
        return render_template('trial.html', data=data)

@app.route('/apiupload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        print(file_path)
        file.save(file_path)
        result = detectFakeVideo("Uploaded_Files/" + file.filename)
        print("Uploaded_Files/" + file.filename)
        os.remove(file_path)
        print(result)
        return jsonify({"success": True, "filename": file.filename, "deepfake": result[0]}), 201



@app.route('/scrape', methods=['POST'])
def scrape_endpoint():
    data = request.json
    url = data.get('url')
    folder_path = 'images'
    csv_file = 'image_data.csv'
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    image_data = scrape_images(url, f"static/{folder_path}")
    save_to_csv(image_data, csv_file)
    
    # Check for deepfakes and update CSV
    check_images_for_deepfakes(csv_file)
    
    # Collect fake images from the CSV file
    fake_images = []
    with open(csv_file, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['Deepfake Flag'] == 'Fake':
                fake_images.append({'url': row['Image URL'], 'path': row['File Path']})

    # Open the index.html page automatically
    webbrowser.open('http://127.0.0.1:3000/deeptab')

    return jsonify({
        'message': 'Scraping and deepfake detection completed',
        'csv_file': csv_file,
        'fakeImages': fake_images
    }), 200

@app.route('/deepfakes', methods=['GET'])
def deepfakes():
    csv_file = 'image_data.csv'
    fake_images = []

    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['Deepfake Flag'] == 'Fake':
                    # Convert image URL to a path accessible by Flask
                    file_path = os.path.join('images', os.path.basename(row['File Path']))
                    fake_images.append({
                       'url': f"images/{ os.path.basename(row['File Path']) }",
                         'path': file_path})
    except Exception as e:
        print(f"Failed to read CSV file: {e}")

    return jsonify(fake_images)

@app.route('/close', methods=['POST'])
def close_endpoint():
    csv_file = 'image_data.csv'
    folder_path = 'static/images'
    
    # Clear the CSV file
    open(csv_file, 'w').close()
    
    # Clear the images directory
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)

    return jsonify({'message': 'Resources cleared'}), 200

@app.route('/deeptab',methods=['GET'])
def deeptab():
    return render_template('deepfakes.html')

def generate_frames():
    webcam = cv2.VideoCapture(0)
    while True:
        success, frame = webcam.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera')
def camera():
    return render_template('camera.html')

@sockets.route('/stream')
def stream(ws):
    while not ws.closed:
        message = ws.receive()
        if message:
            # Convert the received bytes to a NumPy array
            nparr = np.frombuffer(message, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # Decode the image
            
            if frame is not None:
                cv2.imshow("Screen Stream", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    cv2.destroyAllWindows()

@app.route('/streamtab')
def streamtab():
    return render_template('streamtab.html')
        
if __name__ == '__main__':
  app.run(host='0.0.0.0',port=3000, debug=True)



