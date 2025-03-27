(async () => {
    let stream = await navigator.mediaDevices.getDisplayMedia({ video: true });
    let video = document.createElement("video");
    video.srcObject = stream;
    video.play();

    let canvas = document.createElement("canvas");
    let ctx = canvas.getContext("2d");

    let ws = new WebSocket("ws://127.0.0.1:5000/stream");

    video.onplaying = () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        setInterval(() => {
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            canvas.toBlob(blob => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(blob);
                }
            }, "image/jpeg");
        }, 100);
    };

    chrome.runtime.onMessage.addListener((message) => {
        if (message.action === "stop") {
            stream.getTracks().forEach(track => track.stop());
            ws.close();
        }
    });
})();
