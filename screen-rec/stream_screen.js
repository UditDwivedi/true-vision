// Function to capture screen and send via WebSocket
async function captureAndSendVideoStream() {
    try {

        chrome.desktopCapture.chooseDesktopMedia(
        ['screen', 'window', 'tab'],
        async function (streamId) {

          if (streamId == null) {
            return;
          }
        
          // Request screen capture
          const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                        mandatory: {
                            chromeMediaSource: 'desktop',
                            chromeMediaSourceId: streamId,
                        }
                    },
            audio: false
          });
      
          // Create WebSocket connection
          const socket = new WebSocket('ws://localhost:3000');
      
          // Wait for socket to open
          socket.onopen = () => {
            console.log('WebSocket connection established');
            
            // Create media recorder to capture stream
            const mediaRecorder = new MediaRecorder(stream, {
              mimeType: 'video/webm'
            });
      
            // Collect video chunks
            const chunks = [];
            mediaRecorder.ondataavailable = (event) => {
              if (event.data.size > 0) {
                chunks.push(event.data);
              }
            };
      
            // When recording stops, send chunks
            mediaRecorder.onstop = () => {
              const blob = new Blob(chunks, { type: 'video/webm' });
              
              // Convert blob to ArrayBuffer for sending
              const reader = new FileReader();
              reader.onloadend = () => {
                socket.send(reader.result);
              };
              reader.readAsArrayBuffer(blob);
            };
      
            // Start recording
            mediaRecorder.start(1000); // Capture chunks every 1 second
      
            // Optional: Stop recording after a certain time or on user action
            setTimeout(() => {
              mediaRecorder.stop();
              stream.getTracks().forEach(track => track.stop());
            }, 30000); // Stop after 30 seconds
          };
      
          // Handle WebSocket errors
          socket.onerror = (error) => {
            console.error('WebSocket Error:', error);
          };
      
          // Handle socket close
          socket.onclose = () => {
            console.log('WebSocket connection closed');
          };
      
        })

    } catch (e) {
        console.log(e)
    }
}
      