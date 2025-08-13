// Camera handling and WebSocket communication for live feed

class CameraFeed {
    constructor(videoElement, canvasElement, statusElement) {
        this.video = videoElement;
        this.canvas = canvasElement;
        this.statusElement = statusElement;
        this.streaming = false;
        this.ctx = this.canvas.getContext('2d');
        this.apiBaseUrl = window.location.origin;
        this.processingFrame = false;
        this.frameInterval = 500; // Send a frame every 500ms
        this.intervalId = null;
    }

    async start() {
        try {
            this.updateStatus('Requesting camera access...');
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'environment' // Use back camera on mobile if available
                }, 
                audio: false 
            });
            
            this.video.srcObject = stream;
            this.video.play();
            this.streaming = true;
            this.updateStatus('Camera connected');
            
            // Set canvas size once video dimensions are known
            this.video.addEventListener('loadedmetadata', () => {
                this.canvas.width = this.video.videoWidth;
                this.canvas.height = this.video.videoHeight;
            });
            
            // Start sending frames
            this.startFrameCapture();
            
            return true;
        } catch (error) {
            this.updateStatus(`Camera error: ${error.message}`);
            console.error('Camera access error:', error);
            return false;
        }
    }

    stop() {
        if (this.streaming) {
            const stream = this.video.srcObject;
            const tracks = stream.getTracks();
            
            tracks.forEach(track => track.stop());
            this.video.srcObject = null;
            this.streaming = false;
            
            if (this.intervalId) {
                clearInterval(this.intervalId);
                this.intervalId = null;
            }
            
            this.updateStatus('Camera stopped');
            return true;
        }
        return false;
    }

    startFrameCapture() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
        
        this.intervalId = setInterval(() => {
            this.captureAndSendFrame();
        }, this.frameInterval);
    }

    captureAndSendFrame() {
        if (!this.streaming || this.processingFrame) return;
        
        this.processingFrame = true;
        
        // Draw current video frame to canvas
        this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        
        // Get frame as base64 data URL
        const frameData = this.canvas.toDataURL('image/jpeg', 0.8);
        
        // Send frame to server
        this.sendFrameToServer(frameData)
            .then(result => {
                if (result && result.processed) {
                    this.updateDetectionResults(result);
                }
            })
            .catch(error => {
                console.error('Error sending frame:', error);
            })
            .finally(() => {
                this.processingFrame = false;
            });
    }

    async sendFrameToServer(frameData) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/socket`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ frame: frameData })
            });
            
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Frame processing error:', error);
            this.updateStatus(`Processing error: ${error.message}`);
            return null;
        }
    }

    updateDetectionResults(result) {
        // This function would update the UI with detection results
        // Implementation depends on your UI structure
        console.log('Detection results:', result);
        
        // Example: Update a results container
        const resultsContainer = document.getElementById('detection-results');
        if (resultsContainer) {
            // Create a new result entry
            const resultEntry = document.createElement('div');
            resultEntry.className = 'result-entry';
            
            // Format the result
            let resultHTML = `<div class="timestamp">${result.timestamp}</div>`;
            resultHTML += '<div class="detections">';
            
            result.detections.forEach(detection => {
                const statusClass = detection.detected ? 'detected' : 'not-detected';
                resultHTML += `
                    <div class="detection-item ${statusClass}">
                        <span class="type">${detection.type}</span>
                        <span class="confidence">${Math.round(detection.confidence * 100)}%</span>
                    </div>
                `;
            });
            
            resultHTML += '</div>';
            resultEntry.innerHTML = resultHTML;
            
            // Add to results container (at the beginning)
            resultsContainer.insertBefore(resultEntry, resultsContainer.firstChild);
            
            // Limit the number of displayed results
            while (resultsContainer.children.length > 10) {
                resultsContainer.removeChild(resultsContainer.lastChild);
            }
        }
    }

    updateStatus(message) {
        if (this.statusElement) {
            this.statusElement.textContent = message;
        }
        console.log('Camera status:', message);
    }
}

// Export the class
window.CameraFeed = CameraFeed;