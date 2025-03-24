from flask import Flask, render_template, redirect, request, url_for, send_file
from flask import jsonify, json
from werkzeug.utils import secure_filename
from image_scraper.scraper import scrape_images
from image_scraper.csv_handler import save_to_csv
from deepfake_detector import check_images_for_deepfakes
import webbrowser
import csv


import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'

import torch
import torchvision
from torchvision import transforms
from torch.utils.data import DataLoader
from torch.utils.data.dataset import Dataset
import numpy as np
import cv2
import face_recognition

from torch.autograd import Variable

import time

import sys

from torch import nn

from torchvision import models

from skimage import img_as_ubyte
import warnings
warnings.filterwarnings("ignore")

UPLOAD_FOLDER = 'Uploaded_Files'
video_path = ""

detectOutput = []

app = Flask("__main__", template_folder="templates")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class Model(nn.Module):
  def __init__(self, num_classes, latent_dim= 2048, lstm_layers=1, hidden_dim=2048, bidirectional=False):
    super(Model, self).__init__()

    model = models.resnext50_32x4d(weights='ResNeXt50_32X4D_Weights.DEFAULT')

    self.model = nn.Sequential(*list(model.children())[:-2])

    self.lstm = nn.LSTM(latent_dim, hidden_dim, lstm_layers, bidirectional)

    self.relu = nn.LeakyReLU()

    self.dp = nn.Dropout(0.4)

    self.linear1 = nn.Linear(2048, num_classes)

    self.avgpool = nn.AdaptiveAvgPool2d(1)



  def forward(self, x):
    batch_size, seq_length, c, h, w = x.shape

    x = x.view(batch_size*seq_length, c, h, w)

    fmap = self.model(x)
    x = self.avgpool(fmap)
    x = x.view(batch_size, seq_length, 2048)
    x_lstm,_ = self.lstm(x, None)
    return fmap, self.dp(self.linear1(x_lstm[:,-1,:]))




im_size = 112

mean = [0.485, 0.456, 0.406]

std = [0.229, 0.224, 0.225]

sm = nn.Softmax()

inv_normalize = transforms.Normalize(mean=-1*np.divide(mean, std), std=np.divide([1,1,1], std))

def im_convert(tensor):
  image = tensor.to("cpu").clone().detach()
  image = image.squeeze()
  image = inv_normalize(image)
  image = image.numpy()
  image = image.transpose(1,2,0)
  image = image.clip(0,1)
  cv2.imwrite('./2.png', image*255)
  return image

# For prediction of output  
def predict(model, img, path='./'):
  # use this command for gpu    
  # fmap, logits = model(img.to('cuda'))
  fmap, logits = model(img.to())
  params = list(model.parameters())
  weight_softmax = model.linear1.weight.detach().cpu().numpy()
  logits = sm(logits)
  _, prediction = torch.max(logits, 1)
  confidence = logits[:, int(prediction.item())].item()*100
  print('confidence of prediction: ', logits[:, int(prediction.item())].item()*100)
  return [int(prediction.item()), confidence]


# To validate the dataset
class validation_dataset(Dataset):
  def __init__(self, video_names, sequence_length = 60, transform=None):
    self.video_names = video_names
    self.transform = transform
    self.count = sequence_length

  # To get number of videos
  def __len__(self):
    return len(self.video_names)

  # To get number of frames
  def __getitem__(self, idx):
    video_path = self.video_names[idx]
    frames = []
    a = int(100 / self.count)
    first_frame = np.random.randint(0,a)
    for i, frame in enumerate(self.frame_extract(video_path)):
      faces = face_recognition.face_locations(frame)
      try:
        top,right,bottom,left = faces[0]
        frame = frame[top:bottom, left:right, :]
      except:
        pass
      frames.append(self.transform(frame))
      if(len(frames) == self.count):
        break
    frames = torch.stack(frames)
    frames = frames[:self.count]
    return frames.unsqueeze(0)

  # To extract number of frames
  def frame_extract(self, path):
    vidObj = cv2.VideoCapture(path)
    success = 1
    while success:
      success, image = vidObj.read()
      if success:
        yield image


def detectFakeVideo(videoPath):
    im_size = 112
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]

    train_transforms = transforms.Compose([
                                        transforms.ToPILImage(),
                                        transforms.Resize((im_size,im_size)),
                                        transforms.ToTensor(),
                                        transforms.Normalize(mean,std)])
    path_to_videos= [videoPath]

    video_dataset = validation_dataset(path_to_videos,sequence_length = 20,transform = train_transforms)
    # use this command for gpu
    # model = Model(2).cuda()
    model = Model(2)
    path_to_model = 'model/df_model.pt'
    model.load_state_dict(torch.load(path_to_model, map_location=torch.device('cpu')))
    model.eval()
    for i in range(0,len(path_to_videos)):
        print(path_to_videos[i])
        prediction = predict(model,video_dataset[i],'./')
        if prediction[0] == 1:
            print("REAL")
        else:
            print("FAKE")
    return prediction


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
  prediction = detectFakeVideo(video_path)
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
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        result = detectFakeVideo("Uploaded_Files/" + file.filename)
        print("Uploaded_Files/" + file.filename)
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
    folder_path = 'images'
    
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
        
if __name__ == '__main__':
  app.run(host='0.0.0.0',port=3000, debug=True)



