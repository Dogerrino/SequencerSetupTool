#Using Pylon 25.10
#Using PyPylon 4.2.0
# ===============================================================================
#
# ===============================================================================
from pypylon import pylon
from pypylon import genicam

import sys
import os

# Clean the terminal output
def clear():

    # for windows
    if os.name == 'nt':
        _ = os.system('cls')
 
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = os.system('clear')

#Get all cameras -> "devices"
def TryGetDevices():
    devices = tlFactory.EnumerateDevices()
    if len(devices) == 0:
        raise pylon.RuntimeException("No camera present.")
    return devices

#Setup Camera Array
def SetupCameras(devices):
    cameras = pylon.InstantCameraArray(min(len(devices), maxCamerasToUse))
    # Create and attach all Pylon Devices.
    for i, cam in enumerate(cameras):
        cam.Attach(tlFactory.CreateDevice(devices[i]))

        # Print the model name of the camera.
        print("Using device ", cam.GetDeviceInfo().GetModelName())
    return cameras

#Setup Cameras for triggering
def SetupTriggering(cameras, TriggerSettings):
    for cam in cameras:
        #Setup for Triggering
        cam.TriggerSelector.SetValue(TriggerSettings[0])
        cam.TriggerSource.SetValue(TriggerSettings[1])
        cam.TriggerMode.Value = TriggerSettings[2]

#Setup Sequencer Things
def SequencerSetup(camera):

    print("Inside the SequencerSetup")

    # ** Populating the Sequencer Sets **
    # Enable sequencer configuration mode
    camera.SequencerMode.Value = "Off"
    camera.SequencerConfigurationMode.Value = "On"

    # Configure parameters to be stored in the first sequencer set
    camera.Width.Value = 600
    camera.Height.Value = 300
    # Select sequencer set 0 and save the parameter values
    camera.SequencerSetSelector.Value = 0
    camera.SequencerSetSave.Execute()

    # Configure parameters to be stored in the second sequencer set
    camera.Width.Value = 800
    camera.Height.Value = 600
    # Select sequencer set 1 and save the parameter values
    camera.SequencerSetSelector.Value = 1
    camera.SequencerSetSave.Execute()

    # Enable sequencer mode to operate the sequencer
    camera.SequencerMode.Value = "On"

    # ** Configuring sequencer set advance **
    # Assume you want to alternate between sequencer sets 0 and 1 using input line 3
    # Enable sequencer configuration mode
    camera.SequencerMode.Value = "Off"
    camera.SequencerConfigurationMode.Value = "On"
    # Set the start set to set 0
    camera.SequencerSetStart.Value = 0
    # Load and configure sequencer set 0
    camera.SequencerSetSelector.Value = 0
    camera.SequencerSetLoad.Execute()
    camera.SequencerPathSelector.Value = 0
    camera.SequencerSetNext.Value = 1

    print("Using: EnumEntry_SequencerTriggerSource_Line3")
    camera.SequencerTriggerSource.Value = "EnumEntry_SequencerTriggerSource_Line3"#"Line3"
    
    
    camera.SequencerTriggerActivation.Value = "RisingEdge"
    # Save the changes
    camera.SequencerSetSave.Execute()
    # Load and configure sequencer set 1
    camera.SequencerSetSelector.Value = 1
    camera.SequencerSetLoad.Execute()
    camera.SequencerPathSelector.Value = 0
    camera.SequencerSetNext.Value = 2
    camera.SequencerTriggerSource.Value = "Line3"
    camera.SequencerTriggerActivation.Value = "RisingEdge"
    # Save the changes
    camera.SequencerSetSave.Execute()
    
    # Enable sequencer mode to operate the sequencer
    camera.SequencerMode.Value = "On"

#Main Function // Timing the Trigger to Image Availability
def main():
    print("Main")
    try:

        # Create an array of instant cameras for the found devices and avoid exceeding a maximum number of devices.
        devices = TryGetDevices()
        print(f"Length of deivces: {len(devices)}")
        cameras = SetupCameras(devices)
        cameras.Open()

        #Setup for Triggering
        SetupTriggering(cameras, TriggerSettings)

        #Setup Sequencer
        SequencerSetup(cameras[0])

        # Start the grabbing 
        #cameras.StartGrabbingMax(countOfImagesToGrab)
        cameras.StartGrabbing()

        # Camera.StopGrabbing() is called automatically by the RetrieveResult() method
        # when c_countOfImagesToGrab images have been retrieved.
        for i in range(countOfImagesToGrab):

            #LocalVar for this loop
            ThisCamera = i % maxCamerasToUse

            # Wait for an image and then retrieve it. A timeout of 100 ms is used.
            grabResult = cameras[ThisCamera].RetrieveResult(100, pylon.TimeoutHandling_ThrowException)

            # Image grabbed successfully?
            if grabResult.GrabSucceeded():
                print(f"Current Width: ", {ThisCamera.Width.GetValue()})
            else:
                print("Error: ", grabResult.ErrorCode, grabResult.ErrorDescription)
            grabResult.Release()

        #End of Camera Things
        cameras.Close()
        return 0 #exitCode

    except genicam.GenericException as e:
        # Error handling.
        print("An exception occurred.")
        print(e)
        return 1 #exitCode

    #sys.exit(exitCode)

if(__name__):
    #Clean Slate
    clear()

    #Number of cameras to use
    # Limits the amount of cameras used for grabbing.
    # It is important to manage the available bandwidth when grabbing with multiple cameras.
    # This applies, for instance, if two GigE cameras are connected to the same network adapter via a switch.
    # To manage the bandwidth, the GevSCPD interpacket delay parameter and the GevSCFTD transmission delay
    # parameter can be set for each GigE camera device.
    # The "Controlling Packet Transmission Timing with the Interpacket and Frame Transmission Delays on Basler GigE Vision Cameras"
    # Application Notes (AW000649xx000)
    # provide more information about this topic.
    # The bandwidth used by a FireWire camera device can be limited by adjusting the packet size.
    maxCamerasToUse = 1

    # Number of images to be grabbed, per camera.
    countOfImagesToGrabperCamera = 5

    #Total Number of Images to get
    countOfImagesToGrab = countOfImagesToGrabperCamera * maxCamerasToUse

    #Trigger Settings for the Setup
    # Form of           <TriggerSelector>,  <TriggerSource>,    <TriggerMode>
    TriggerSettings = [ "FrameStart",       "Software",         "Off"         ]

    #Camera Information
    # BaslerUsb for USB; 
    # BaslerGigE for GigE
    # BaslerGTC/Basler/CXP for CXP 
    info = pylon.DeviceInfo()
    info.SetDeviceClass('BaslerUsb')

    # Get the transport layer factory.
    tlFactory = pylon.TlFactory.GetInstance()

    #Actual Main
    exitCode = main()

    #End things
    sys.exit(exitCode)