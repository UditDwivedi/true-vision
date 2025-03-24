import os
import csv

def save_to_csv(image_data, csv_file):
    try:
        file_exists = os.path.isfile(csv_file)
        
        with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            if not file_exists:
                writer.writerow(['Image URL', 'File Path', 'Deepfake Flag'])
            
            for row in image_data:
                writer.writerow(row)
        
        print(f"Data saved to {csv_file}")
    except Exception as e:
        print(f"Failed to save data to CSV: {e}")

def update_csv_flag(csv_file, rows):
    try:
        with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Image URL', 'File Path', 'Deepfake Flag'])  # Ensure header is written
            writer.writerows(rows)
        
        print(f"CSV file {csv_file} updated successfully.")
    except Exception as e:
        print(f"Failed to update CSV file: {e}")
