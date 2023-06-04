# TreeRez
## Simple commandline utility to copy & resize TIFF scans
To apply machine learning or deep learning to the BB-Collection for automatic correction of rotation, flipping, segmentation, etc., a subset of the scans must be prepared as a training set. For performance reasons, the resolution of the training set should be lower than that of the original.  
Furthermore, the scans should be examined and any large borders removed to enhance the effectiveness and improve the scoring potential of the trained models.  

TreeRez lets you randomly sample a subset of patient folders, copying and resizing TIFF scans, automatically trimming white borders and converting them to RGB PNGs.
### Install
create a python env as usual (venv, pipenv, conda, etc..)

```pip install -r requirements.txt```
### HowTo
```
python treerez.py -h

usage: treerez.py [-h] [-n] [-r] [-q] [-t] source destination

positional arguments:
  source              source folder - contains patients folders with xray-scans
  destination         destination folder - sampled xray-scans will be copied and resized here

options:
  -h, --help          show this help message and exit
  -n, --dryrun        Do nothing, dry run
  -r , --resolution   target resolution for copied xray-scans (default: 1024)
  -q , --quantity     number of sampled patients (default: 1)
  -t , --trim         auto-trimming threshold - from 0 (black) to 255 (white) (default: 240)
```

You can find more details in the [treerez logbook](/documentation/treerez_logbook.ipynb).
