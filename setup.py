from distutils.core import setup
from sys import version
import glob

if int(version.split('.')[0]) > 2:
    print "No support for python 3"
    exit(1)
    
setup(name="EagleEye",
    version="0.1",
    author="Gwilyn Saunders, Kin Kuen Liu, Manjung Kim",
    packages=[
        'eagleeye', 
        'serial', 
        'elementtree', 
        'custom_widgets'
    ],
    package_data={
        'serial': ['*.txt'],
        'elementtree': ['*.txt'],
    },
    data_files=[
        ('', ['eagleeye_v2.dtd', 'eagleeye.cfg', 'wizard.ui']),
        ('vicon_binaries', glob.glob('vicon_binaries/*.'))
    ],
    py_modules=[
        'wizard', 
        'extract_frames', 
        'mapping',
        'trainer',
        'compare', 
        'stdcalib',
        'vicon_capture',
        'icons_rc'
    ])
