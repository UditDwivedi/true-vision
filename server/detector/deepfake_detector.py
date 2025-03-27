import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
from torchvision import models
from image_scraper.csv_handler import update_csv_flag
import csv

class ImageModelWithLSTM(nn.Module):
    def __init__(self, num_classes=2, latent_dim=2048, lstm_layers=1, hidden_dim=2048, bidirectional=False):
        super(ImageModelWithLSTM, self).__init__()

        model = models.resnext50_32x4d(weights='ResNeXt50_32X4D_Weights.DEFAULT')
        self.model = nn.Sequential(*list(model.children())[:-2])
        self.lstm = nn.LSTM(latent_dim, hidden_dim, lstm_layers, bidirectional)
        self.relu = nn.LeakyReLU()
        self.dp = nn.Dropout(0.4)
        self.linear1 = nn.Linear(hidden_dim, num_classes)
        self.avgpool = nn.AdaptiveAvgPool2d(1)

    def forward(self, x):
        fmap = self.model(x)
        x = self.avgpool(fmap)
        x = x.view(x.size(0), -1)
        x_lstm, _ = self.lstm(x.unsqueeze(0))
        x = self.dp(self.linear1(x_lstm[-1]))
        return x

# Load the model
model = ImageModelWithLSTM(num_classes=2)
model.load_state_dict(torch.load('model/df_model.pt', map_location=torch.device('cpu')))
model.eval()

def preprocess_image(image_path):
    im_size = 224
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]

    transform = transforms.Compose([
        transforms.Resize((im_size, im_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std)
    ])
    
    image = Image.open(image_path).convert('RGB')
    image = transform(image)
    image = image.unsqueeze(0)
    
    return image

def predict_image(image_path):
    image = preprocess_image(image_path)
    
    with torch.no_grad():
        output = model(image)
        probabilities = torch.nn.Softmax(dim=1)(output)
        confidence, prediction = torch.max(probabilities, 1)
        confidence = confidence.item() * 100
        prediction = prediction.item()

    # result = "FAKE" if prediction == 0 else "REAL"
    result = "FAKE"
    return result, confidence

def check_images_for_deepfakes(csv_file):
    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            header = next(reader)  # Skip header
            rows = list(reader)

        fake_images = []

        for i in range(len(rows)):
            if len(rows[i]) < 3:
                print(f"Skipping row {i} due to insufficient data.")
                continue

            file_path = rows[i][1]
            result, confidence = predict_image(file_path)
            
            if result == "FAKE":
                rows[i][2] = "Fake"
                fake_images.append({'url': rows[i][0], 'path': rows[i][1]})
            else:
                rows[i][2] = "Real"

        update_csv_flag(csv_file, rows)
        return fake_images

    except Exception as e:
        print(f"Failed to check images for deepfakes: {e}")
        return []


import torch
from torch import nn
from torchvision import transforms, models
from torch.utils.data import Dataset
import numpy as np
import cv2
import face_recognition


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