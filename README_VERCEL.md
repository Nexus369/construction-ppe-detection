# Construction PPE Detection System - Vercel Deployment with Live Camera Feed

This project has been adapted for deployment on Vercel with support for live camera feed functionality. The system uses client-side camera access and serverless functions to provide real-time PPE detection.

## Features

- **Live Camera Feed**: Access the user's camera directly in the browser
- **Real-time Detection**: Process camera frames in real-time using serverless functions
- **Responsive UI**: Modern interface that works on desktop and mobile devices
- **Detection Logging**: View and track PPE compliance in real-time

## How It Works

1. **Client-Side Camera Access**: The application uses the browser's MediaDevices API to access the user's camera
2. **Frame Capture**: Frames are captured at regular intervals and sent to the serverless API
3. **Serverless Processing**: Each frame is processed by a serverless function that returns detection results
4. **Real-time Updates**: Detection results are displayed in the UI as they are received

## Deployment

Follow the instructions in the `VERCEL_DEPLOYMENT.md` file to deploy this project to Vercel.

## Technical Implementation

### Key Files

- `js/camera.js`: Handles camera access and frame processing
- `api/socket.py`: Serverless function that processes camera frames
- `visit-site.html`: The live monitoring interface
- `vercel.json`: Configuration for Vercel deployment

### Browser Compatibility

This implementation uses modern web APIs and should work in all recent versions of:

- Chrome
- Firefox
- Edge
- Safari (iOS 14.3+ and macOS)

## Security Considerations

- Camera access requires explicit user permission
- All communication with the API is secured via HTTPS
- No camera data is stored permanently

## Limitations

- Processing occurs in the cloud, so there may be some latency
- Camera access requires a secure context (HTTPS)
- Mobile browsers may have varying levels of support for camera APIs

## Local Development

To test the application locally:

1. Install the Vercel CLI: `npm i -g vercel`
2. Run `vercel dev` in the project directory
3. Open the local development URL in your browser