# Detect motion using web camera and display notification

## How to use
Run server.py. You can add "--help" parameter to see possible options (HTTP port number, threshold (sensitivity) and SSL if needed).

    server.py -p 8000 -s 100000

Open html page in a browser specifying the host where the server runs and the port number:

    http://localhost:8000/index.html

Notification should be shown (message box on Windows or console output on other platforms) when camera captures any motion. 

## How it works
Html page + JavaScript captures video frames from the camera. Each video frame is compared against the previous one and difference is calculated as a number (greater difference makes greater number). Those numbers are sent (HTTP POST) to the server which serves the page itself. The server analyzes received numbers and if some number is greater than specified threshold then a notification is displayed. 

Server is implemented in python using standard python libraries. Supported platforms - any with modern browser (for client side) and any with python installed (for server side). Tested on Windows/linux/android and python 2.7.

## Regards
Thanks to Benjamin Horn for this [article](https://benjaminhorn.io/code/motion-detection-with-javascript-and-a-web-camera/) and [code](https://github.com/beije/motion-detection-in-javascript).