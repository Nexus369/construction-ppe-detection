# Deploying Construction PPE Detection System on Vercel

This guide explains how to deploy the Construction PPE Detection System on Vercel, a cloud platform for static sites and serverless functions.

## Prerequisites

- A GitHub account
- A Vercel account (you can sign up at [vercel.com](https://vercel.com) using your GitHub account)
- Your project pushed to a GitHub repository

## Deployment Steps

### 1. Push Your Code to GitHub

Make sure your project is pushed to GitHub. If you haven't done this yet, follow these steps:

```bash
git add .
git commit -m "Prepare for Vercel deployment"
git push origin main
```

### 2. Import Your Project on Vercel

1. Log in to your Vercel account
2. Click on "New Project"
3. Import your GitHub repository
4. Configure the project settings:
   - Framework Preset: Other
   - Root Directory: ./
   - Build Command: Leave empty
   - Output Directory: Leave empty

### 3. Environment Variables

No environment variables are required for the basic deployment.

### 4. Deploy

Click the "Deploy" button and wait for the deployment to complete.

## Project Structure for Vercel

The project has been adapted for Vercel deployment with the following structure:

- `vercel.json`: Configuration file for Vercel deployment
- `api/index.py`: Serverless API endpoint that handles requests
- `js/main.js`: Updated to work with serverless API endpoints
- `index.html` and `visit-site.html`: Static frontend files

## Live Camera Feed on Vercel

This deployment includes support for live camera feed using the following approach:

1. **Client-side Camera Access**: The browser accesses the user's camera using the MediaDevices API
2. **Frame Processing**: Captured frames are sent to the serverless API endpoint
3. **Real-time Detection**: The API processes frames and returns detection results

### How It Works

1. When you click "Start Detection" on the live monitor page, the application requests camera access
2. Frames are captured at regular intervals and sent to the `/api/socket` endpoint
3. The serverless function processes each frame and returns detection results
4. Results are displayed in the detection log in real-time

## Limitations of the Vercel Deployment

1. **Browser Permissions**: Users must grant camera access permissions in their browser

2. **Processing Delay**: Since frames are processed in the cloud, there may be some latency

3. **No Persistent State**: Being serverless, the application doesn't maintain state between requests. Each request is processed independently.

4. **Cold Starts**: Serverless functions may experience "cold starts" where the first request takes longer to process.

## Local Development

To test the Vercel deployment locally, you can use the Vercel CLI:

```bash
npm i -g vercel
vercel dev
```

This will start a local development server that mimics the Vercel production environment.

## Troubleshooting

- If you encounter deployment errors, check the Vercel deployment logs for details.
- Make sure your `vercel.json` file is correctly configured.
- Ensure that all required files are included in your repository.

## Alternative Deployment Options

If you need full functionality with camera access and persistent state, consider:

1. Deploying on a VPS (Virtual Private Server) like DigitalOcean, AWS EC2, or Google Compute Engine.
2. Using a container platform like Heroku or Google Cloud Run.
3. Setting up a local server on your network.