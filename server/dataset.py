import os
import shutil
import random

root_dir = 'Dataset'
small_dir = 'DatasetSmall'

for fol in ['Test', 'Train', 'Validation']:

    for type in ['Fake', 'Real']:
        if not os.path.exists(os.path.join(small_dir,fol,type)):
            os.makedirs(os.path.join(small_dir,fol,type))

        for file in os.listdir(os.path.join(root_dir,fol,type)):
            if random.random() <= 0.5:
                shutil.copyfile(os.path.join(root_dir,fol,type,file), os.path.join(small_dir,fol,type,file))
    
