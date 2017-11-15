# Copyright 2017 Stanislav Pidhorskyi
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#  http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Download all needed data to start training the network"""

import os
from utils.download import download

data_path = "data/"

download(directory=data_path, url="https://www.cs.toronto.edu/~kriz/cifar-10-binary.tar.gz", extract_targz=True)
download(directory=data_path, google_drive_fileid="0B3kP5zWXwFm_OUpQbDFqY2dXNGs", file_name="imagenet-vgg-f_old.mat")
#download(directory=data_path, url="http://www.vlfeat.org/matconvnet/models/imagenet-vgg-f.mat")
nus_wide = os.path.join(data_path, "nus_wide")
download(directory=nus_wide, google_drive_fileid="1yf6KqG8aQAdqAAl1I-stoGpecyct-NZD", extract_zip=True)
imagenet = os.path.join(data_path, "imagenet")
download(directory=imagenet, google_drive_fileid="1NwcXyI-Bqoty_T9mWfpEuyPJImXjo6pT", extract_zip=True)
