Eagle Eye Project
=================

1 Overview
----------
TODO, introduce problem, describe solution, outputs, application, deliverables

### 1.1 Team
__ITMS__

- Gwilyn Saunders
- Kin Kuen Liu
- Manjung Kim

__Engineering__

- Peter Barsznica

__Supervisors__

- Victor Stamatescu
- Russell Brinkworth


### 1.2 Legal
-   The all-scientific CRAP License
-   <http://matt.might.net/articles/crapl/CRAPL-LICENSE.txt>


### 1.3 Prerequisites
Please ensure all software dependencies are the same architecture
(32 or 64-bit). The PyVicon library is built for a 32-bit Vicon Tracking System.
So unless you want to be recompiling it (you don't), stick to 32-bit.

- Windows 7+
- Python 2.7 (Anaconda)
- PyQt 4.11 (Qt 4.8.7)
- OpenCV 3.0
- *For Capture*
  - Vicon Tracker System (v1.2 32-bit)
  - Serial RS232 Serial connection
  - [Flash Sync circuit](3-1-4-flash-sync-circuit)
  - A camera flash w/ PC-SYNC connection


### 1.4 Install instructions

Download and install the pre-requisities:
- [Anaconda](https://repo.continuum.io/miniconda/Miniconda-latest-Windows-x86.exe)
- [PyQt](http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.11.4/PyQt4-4.11.4-gpl-Py2.7-Qt4.8.7-x32.exe/download)
- [OpenCV](http://sourceforge.net/projects/opencvlibrary/files/opencv-win/3.0.0/opencv-3.0.0.exe/download)

TODO copy instructions for opencv-ffmpeg and cv2.pyd


#### 1.4.1 Re-compiling PyVicon
You really shouldn't need to do this unless you're not using a different 
Vicon Tracker than the one at the UniSA Mawson Lakes campus.

TODO


2 Pipeline Overview
-------------------
![Data Flow](assets/dataflow.png)

TODO description


3 Core Tools
------------

### 3.1 Vicon Capture
This tool records object positional data into [CSV files](#5-1-raw-dataset-csv) 
from the Vicon system. It includes quality verification and time synchronisation data.

__Preparation__

The Vicon system captures objects that are defined as unique "constellations"
of dots placed on physical objects within the lab. These objects are configured
in the *Vicon Tracker* software. Some experimental/working objects are
stored in the [data/objects](data/objects) folder.

Ensure your running time is sufficient, modify via the command line option or
within the [config file](#6-1-Capture). 

Ensure the correct serial port is defined in the config file.
A list of available serial ports can be found with this command:
``` sh
$ python -m serial.tools.list_ports
```

__Procedure__

The camera must not be moved between the calibration and capture steps. Thankfully, 
the Ricoh Theta m15 can be remotely triggered via a smart phone or tablet.

The tool will capture all active objects in the *Vicon Tracker* software. Be sure to
only enable the objects for a given scenario.

1. Ensure all preparations steps are completed
2. Prepare the camera for recording
3. Run the software (either by GUI or command line)
4. After the first flash, start the camera recording
5. The flash will trigger again, now start perform the scenario
6. The last flash will signal the end of the dataset
7. Stop the camera recording
8. Check the output folder that the objects are all recorded

__Command line Usage__

```sh
$ python vicon_capture.py {-output <folder> | -time <in minutes> | -config <file> | -training <file>}
```

#### 3.1.1 Flash Sync Circuit
This is a circuit by design of Peter Barsznica that triggers a camera flash when
signalled from a serial connection to the computer. This matches the flash data
fields in the CSV file in order to syncronise the video and data feeds.

__This is the circuit detail__

![Circuit Sync](assets/sync_circuit_3.png)

__The circuit connects to the serial GND and CTS pins__

![Serial Pinout](assets/pinouts_serial.gif)


#### 3.1.2 Synchronisation
When running the software, the flash will trigger 3 times. This is a uncorrectable
side-effect of the hardware, therefore the software will delay a number of frames
(as specified in the [config file](#6-1-Capture)) before the first flash is triggered.
There are still only 2 flashes recorded into the CSV.



### 3.2 Calibration
A Camera Calibration Tool based on the OpenCV Library. This script detects 
chessboard pattern from a set of images and determines the intrinsic and distortion
parameters of the camera lens. It can highlight the corners of the chessboards, 
provide an estimated error and sample rectified images.

__Preparation__

TODO

__Procedure__

TODO

__Command line Usage__

```sh
$ python stdcalib.py -output <file path> <multiple jpg files> {-chess_size <pattern: def. 9,6> | -square_size <in mm: def. 1.0> | -preview <preview file folder> | -config <file>}
```


### 3.3 Trainer
This tool creates a training set for the Mapping tool, using Vicon Wand positional
data (from Vicon) and corresponding video capture. This is used to calculate the
extrinsic parameters of the camera, and therefore its pose within the room.

__Preparation__

TODO

__Procedure__

TODO

__Command line Usage__

```sh
$ python trainer.py <video file> <csv file> <data out file> {<mark_in> <mark_out> | -clicks <num_clicks> | -config <file>}
```


### 3.4 Mapping
This software applies mapping routines to convert 3D raw data into 2D datasets 
using models from the Training and Calibration tools.

__Preparation__

TODO

__Procedure__

TODO

__Command line Usage__

```sh
$ python mapping.py -calib <calib xml> -trainer <trainer xml> -output <output dataset> [<multiple csv files>] {--config <file>}
```



### 3.5 Annotation
Takes raw camera footage or images from the Ricoh theta and applies automated 
object detection algorithms. Includes manual adjustment of the annotations.
Outputs an annotated video or image, depending on the input as well as an XML
Dataset - of identical format to the Mapping Tool.

__Preparation__

TODO

__Procedure__

TODO

__Command line Usage__

```sh
$ python annotation.py
```


### 3.6 Evaluation
TODO description

__Preparation__

TODO

__Procedure__

TODO

__Command line Usage__

```sh
$ python eval.py <annotated dataset> <mapped dataset>
```


4 Utility Tools
---------------
TODO description

### 4.1 Wizard
TODO description

__Usage__

```sh
$ python wizard.py
```

Or generate a new shortcut with `gen_shortcut.bat`. This will produce a 
_EagleEye Wizard_ file. Double click the shortcut.

Be sure to re-generate the shortcut if you move the project folder.


### 4.2 Chessboard Extractor
TODO description

__Procedure__

TODO

__Command line Usage__

```sh
$ python extract_frames.py <video file> <output image folder> {-prefix <output name> | -config <file>}
```


### 4.3 Trainer Comparison
TODO description

__Procedure__

TODO

__Command line Usage__

```sh
$ python compare_trainer.py <video file> <mapper xml> <trainer xml> {<mark_in> <mark_out> | -config <file> | -export <file>}
```


### 4.4 Dataset Comparison
TODO description

__Procedure__

TODO

__Command line Usage__

```sh
$ python compare.py <video file> <xml dataset> <xml dataset> {<mark_in> <mark_out> | -config <file> | -export <file>}
```


5 Data Formats
--------------

### 5.1 Raw Dataset CSV
This is object data represented in the Vicon World Coordinates. Each file
contains data for a single object captured. Containing positional, rotational,
sychronisation and marker data.

| Column | Data        | Type  | Examples |
|--------|-------------|-------|----------|
| 0      | Timestamp   | float | 0.144    |
| 1      | Sync        | char  | F, .     |
| 2      | X-axis      | float | 5121.54  |
| 3      | Y-axis      | float | 1543.33  |
| 4      | Z-axis      | float | 45.1431  |
| 5      | X-rotate    | float | 0.1123   |
| 6      | Y-rotate    | float | 0.2323   |
| 7      | Z-rotate    | float | 2.1102   |
| 8      | Max Markers | int   | 5        |
| 9      | Visible     | int   | 4        |


__Synchronisation__

-   . (dot) - is a regular frame
-   F - is a flash frame, there should only be 2 of these within a dataset

__Rotation__

The rotational X, Y, Z is a
[Euler Vector](https://en.wikipedia.org/wiki/Axis%E2%80%93angle_representation),
not to be mistaken with Euler Angles - pitch, yaw, roll.


### 5.2 Calibration XML
TODO description

``` xml
<?xml version='1.0'?>
<StdIntrinsic>
    <CamMat cx="487.032967037" cy="444.164482209" fx="287.98587712" fy="295.556664123" />
    <DistCoe c1="0.0" c2="0.0" c3="0.0" c4="0.0" k1="-0.0206585491055" k2="0.00849952958576" k3="0.00380032047972" k4="0.0861709048126" k5="-0.00205536510651" k6="0.00844339783038" p1="0.00238980715215" p2="-0.00029672399339" />
    <Error arth="0.426145384461" rms="3.32043177324" total="11.5059253805" />
</StdIntrinsic>
```

### 5.3 Trainer XML
TODO description

``` xml
<?xml version='1.0'?>
<TrainingSet>
    <video file="wand_right.avi" />
    <csv file="2015-08-27_13-24_Wand.csv" />
    <frames>
        <frame num="46">
            <plane x="252" y="567" />
            <vicon x="6604.76905818057" y="1225.0367491552" z="71.7138299051588" />
        </frame>
        <frame num="101">
            <plane x="453" y="673" />
            <vicon x="6259.08569084885" y="1905.83353105066" z="69.601629741746" />
        </frame>
    </frames>
</TrainingSet>
```

### 5.4 Dataset XML
TODO description

``` xml
<?xml version='1.0'?>
<dataset>
    <frameInformation>
        <frame number="1" />
        <object id="1" name="EE1">
            <boxinfo height="99" width="99" x="572.190673828" y="425.731567383" />
            <centroid x="622.191" y="475.732" />
        </object>
    </frameInformation>
</dataset>
```

### 5.5 Evaluation XML
TODO

### 5.6 Header XML
TODO description

``` xml
<?xml version='1.0'?>
<datasetHeader date="2015-08-27" name="August27">
    <calibration>
        <xml>calibration.xml</xml>
        <chessboards path="chessboards/" size="4">
            <file>Backside_10.jpg</file>
            <file>Backside_11.jpg</file>
            <file>Backside_12.jpg</file>
            <file>Backside_14.jpg</file>
        </chessboards>
    </calibration>
    <training>
        <xml>training.xml</xml>
        <video mark_in="28" mark_out="667">wand_right.avi</video>
        <csv>2015-08-27_13-24_Wand.csv</csv>
        <map>training_map.xml</map>
    </training>
    <rawData>
        <video mark_in="32" mark_out="721">august27_right.avi</video>
        <vicon path="vicondata/" size="1">
            <file>2015-08-27_13-27_EE1.csv</file>
        </vicon>
    </rawData>
    <datasets>
        <mapping>dataset_mapping.xml</mapping>
        <annotation>dataset_annotation.xml</annotation>
    </datasets>
    <evaluation>august27-evaluation.xml</evaluation>
    <comparison>august27-compare.avi</comparison>
</datasetHeader>
```


6 Configuration
---------------
TODO description

### 6.1 Capture
| Setting           | Default        |
|-------------------|----------------|
| ip_address        | 192.168.10.1   |
| port              | 801            |
| date_format       | Y-%m-%d\_%H-%M |
| flash_delay       | 180            |
| framerate         | 44.955         |
| default_time      | 180            |
| default_output    | data/raw       |
| output_delimiter  | ,              |
| serial_device     | COM4           |
| run_serial        | True           |
| trainer_target    | Wand           |

### 6.2 Trainer
| Setting           | Default        |
|-------------------|----------------|
| font_scale        | 0.4            | 
| font_thick        | 1              | 
| font_colour       | (255,255,255)  |
| buffer_size       | 50             | 
| default_clicks    | 9999           | 
| quality_mode      | 1              | 
| quality_threshold | 0.6            | 
| min_reflectors    | 4              | 
| check_negatives   | on             | 

### 6.3 Mapper
| Setting           | Default        |
|-------------------|----------------|
| min_reflectors    | 4              | 
| check_negatives   | on             | 
| pnp_flags         |                | 

### 6.4 Calibration
| Setting           | Default        |
|-------------------|----------------|
| default_squares   | 1.0            | 
| default_chess     | (9,6)          | 
| calib_flags       |                | 

### 6.5 Compare
| Setting           | Default        |
|-------------------|----------------|
| buffer_size       | 50             | 
| xml1_colour       | (255,255,255)  |
| xml2_colour       | (255,255,255)  |
| fourcc            | DIVX           | 

### 6.6 Compare Trainer
| Setting           | Default        |
|-------------------|----------------|
| font_scale        | 0.4            | 
| font_thick        | 1              | 
| font_colour       | (255,255,255)  |
| buffer_size       | 50             | 
| trainer_colour    | (0,255,0)      |
| mapper_colour     | (255,255,255)  |
| object_target     | Ewad1          | 
| fourcc            | DIVX           | 

### 6.7 Chessboard Extractor
| Setting           | Default        |
|-------------------|----------------|
| buffer_size       | 50             | 
| split_side        | right          | 
| rotate            | r270           | 
| crop              | (0, 0, 120, 0) |
| font_size         | 0.4            | 
| font_thick        | 1              | 
| font_colour       | (255,255,255)  |
