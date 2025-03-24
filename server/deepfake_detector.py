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
