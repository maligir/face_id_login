
# Windows Custom Credential Provider with Face Recognition

This guide will help you install and implement a custom Credential Provider for the Windows login system, using Microsoft's sample code as a base and extending it to communicate with a Python script that performs face recognition. The guide assumes that you have a working Python script for face recognition, that communicates its results through a server socket.

**Please note:** Registering or unregistering DLLs can cause instability for your machine and prevent you from logging into your Windows machine. Always back up your data or use a virtual machine with a separate OS to minimize the risk of corrupting your machine. This guide and the code are provided as is, with no liability for damages or misuse.

## Setup

1. (Optional but recommended) Set up a virtual machine with Windows 10. You will need to find a copy of a Windows OS ISO and enable (VT-x) virtualization in your BIOS.
2. Download the sample Credential Provider code from [this GitHub repository](https://github.com/pauldotknopf/WindowsSDK7-Samples/tree/master/security/credentialproviders). This code is compatible with Visual Studio 2019, as described in the next step.
3. Download Visual Studio 2019 Community edition. During installation, make sure to include the "Desktop development with C++" workload. This will provide you with the necessary tools for building the sample code.
4. Open the solution file (`CredentialProvdersSamples.sln`) in Visual Studio.
5. Set your configuration to your corresponding System type (x86 or x64) by right clicking the desired project(s)->properties->Configuration Properties and setting Configurations and platform accordingly.
6. Build the solution by right-clicking your project(s) and selecting 'Build solution'.
7. Find the DLL in the directory `.../credentialproviders/x64/release/` (or `.../credentialproviders/Win32/Debug/` for 32-bit machines).
8. Move the desired DLL of the credential provider you wish to install into your System32 folder (Typically in the following directory: C:\Windows\System32).
9. Use the .reg file located in your respective project folder to register your DLL and have it show up in your windows log on (…/credentialproviders/samplecredentialprovider/Register.reg). A Unregister.reg file is also located within the same directory if you want to unregister your DLL.
10. Log out to the windows login screen and your custom credential provider should supply their custom user tiles.

## Python Script

The Python script is part of a face recognition server. It utilizes several popular Python libraries such as MTCNN, Keras-VGGFace, SciPy, NumPy, Pillow, Matplotlib, and OpenCV to detect, analyze, and verify faces from images. It also leverages Python's built-in socket library to communicate the face recognition results.

When started, the script initializes a `FaceVerification` class instance that loads the Multi-task Cascaded Convolutional Networks (MTCNN) model for face detection and the VGGFace model with a ResNet50 architecture for face recognition.

The main `run` method of the `FaceVerification` class opens a video capture stream, reads frames from the video stream, and saves a frame as a .jpg file every 120 frames. It detects faces and computes their embeddings (numeric representations). If the face embeddings from the most recent frames match the embeddings of a pre-specified default face image within a certain threshold, the face is recognized. When a match is detected, the script sends a 'Face recognized!' message via a socket connection to the localhost on port 12345. The script stops either after a match is detected or after a maximum limit of iterations (frames) is reached. The script also cleans up any created .jpg files after completion.

To integrate this script with the custom Credential Provider, the `GetSerialization` function in the `CSampleCredential.cpp` file should connect to the Python script's server socket and read the message sent by the Python script. If the message indicates that the face has been recognized, the function should then retrieve the associated username and password. For instance, this might involve reading from a secure file or database which maps recognized faces to Windows usernames and passwords.

Before you start using this script, you need to have a Python environment with all the necessary libraries installed. It is recommended to use a Python virtual environment to avoid conflicts between different versions of libraries. You also need to ensure that your Python environment has access to your computer's camera for the face recognition feature to work properly.

## Extending the Sample Code

To extend the sample Credential Provider to communicate with your Python script, you will primarily need to modify the CSampleCredential.cpp and CSampleProvider.cpp files.

In `CSampleCredential.cpp`, you need to:

1. Modify the `GetSerialization` function to return the username and password acquired from your face recognition script.
2. Create a function to connect to your Python script's server socket, using the Winsock library. This function should read the message sent by the Python script, and if the message indicates that the face has been recognized, it should retrieve the associated username and password.
3. Call this function from `GetSerialization`, before retrieving the username and password.

In `CSampleProvider.cpp`, you may need to make modifications if you want to change how credentials are enumerated or represented. However, in most cases, the main modifications will be in `CSampleCredential.cpp`.

Remember to run your code with administrator privileges, as Credential Providers are part of the Windows security infrastructure.

## References

- [Starting to build your own credential provider](https://blogs.msmvps.com/alunj/2011/02/21/starting-to-build-your-own-credential-provider/)
- [Sharing folders/files between your local drive and your virtual machine (VirtualBox)](https://operating-systems.wonderhowto.com/how-to/share-local-drives-and-folders-using-oracle-vm-virtualbox-with-guest-windows-os-0126237/)
- [Credential Providers in Windows 10](https://msdn.microsoft.com/en-us/library/windows/desktop/mt158211(v=vs.85).aspx)
- [Credential Provider Technical Reference](http://go.microsoft.com/fwlink/?LinkId=717287)
- [Windows Custom Credential Provider Short Guide](https://github.com/bgyoo970/Windows-Custom-Credential-Provider-Short-Guide)
