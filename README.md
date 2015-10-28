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
- Numpy 1.9.3
- PIL 2.8.1 
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

1. You need to prepare an initial video file to annotate.
2. To use automatic annotation, you need to use the semi-automatic tool first to input a xml file.
3. Using the marker tool, you need to get the mark_in and mark_out frame numbers, then pass the values into the command line argument.
Otherwise, it will record entire data into the xml, from beginning of the video to end of the video.
The mark_in and mark_out values indicate where to add. It adds the frame between mark_in + 1 frame, and mark_out frame into the XML.

__Procedure__

1. Run the annotation tool. (python annotation.py) No need to type mark_in and mark_out at this moment.
2. Click "Open semi-automatic tool" button from the main GUI.
3. Click "Split frames from video" button and select the initial video file from the preparation 1.
4. Select the folder to store frames, it will take 1-2 minutes to output frames from the video.
5. Click "Import image frames" button and select the folder from step 4 above.
6. Semi-automatically annotate the object by drawing rectangles. The index of object will be stacked, starting from 1.
Click "draw" button to draw rectangle, and Click "draw" button to drag existing rectangle.
Click "undo" button to undo drawing, and Click "redo" button to redo drawing.
7. Click "Next" button until the object moves, and if you think the object is out from the previous rectangle, repeat step6.
(Usually you should repeat step6 per 15 frames, but if object doesnt move, you dont need to do.)
(Or if the movement of object is huge, for example if object was "buttonside" at previous frame and moved to "backside" in current frame, repeat step6.)
8. Click "Update XML File" button to save the semi-automatic results into a XML file, specify location to save.
9. Run the annotation tool again with the full command line argument. ($ python annotation.py -mark_in <markinframe number> -mark_out <markoutframe number>)
10. Click "Automatic annotation" button from the main GUI.
11. It will say "Please select file". Just Click "Ok" button 
12. It will pop-up a file dialog named as "Please select your video file". Select your initial video file from the preparation 1 and click open button.
13. It will pop-up a file dialog named as "Please select your XML file if possible". Select your input xml file from the step 8 and click open button.
14. It will pop-up a file dialog named as "Please select output filename to save the file". Specify your output video file name, check location and click save button.
15. Click "OK" button to start automatic annotation, the annotation time depends on the size of video, but usually it takes 1-2 minutes.
16. Once the annotation has been completed, it will pop-up a message, just click "OK" button.
17. It will pop-up a file dialog named as "Please write output xml filename to save the dataset". Specify your output xml file name, check location and click save button.
The output xml file from above will be used in the comparision tool.
18. Check the output video file to see how annotation works.
19. If you are not happy with the performance of output video file, you can re-use the semi-automatic tool from step 2. 
20. You can either update the "input" xml file from step 8, or "output" xml file from step 17. (However, updating output xml file from step17 doesnt improve automatic annotation.)
21. In case of updating "input" xml file, from step8, will improve the performance of automatic annotation. Go back to step 2 and do step5.
Click "Import XML File" button and open the xml file from step 8. Review-the output annotated video, and go to the frame which was not happy for you.
Manually specify the objects again, and once you finish that, click "Update XML File" button, it will overwrite the imported XML file.
Do step 9 again, and use the updated "input" XML File.
22. In case of updating "output" xml file, from step8, the xml file will be used in another button called "Annotation from XML".
This case does not improve the performance of automatic annotation, because the button does not contain automatic annotation.
It just converts the XML file to the video.
This case is for only when step 21 does not work properly.
Click "Import XML File" button and open the xml file from step 17. Review-the output annotated video, and go to the frame which was not happy for you.
Manually specify the objects again, and once you finish that, click "Update XML File" button, it will overwrite the imported XML file.
Do step 9 again, and use the updated "output" XML File.

__Command line Usage__

```sh
$ python annotation.py -mark_in <markinframe number> -mark_out <markoutframe number>
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
