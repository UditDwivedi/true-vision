const startMonitoring = async() => {
    const tabs = await chrome.tabs.query({ 'active': true, 'currentWindow': true });
    const currenttab = tabs[0];

    chrome.desktopCapture.chooseDesktopMedia(
        ['screen', 'window', 'tab'],
        function (streamId) {
            if(streamId == null){
                return;
            }
            
            navigator.mediaDevices.getUserMedia({
                audio: false,
                video: {
                    mandatory: {
                        chromeMediaSource: 'desktop',
                        chromeMediaSourceId: streamId
                    }
                }
            }).then((stream) => {

                const mediaRecorder = new MediaRecorder(stream);
                
                let chuncks = []

                mediaRecorder.ondataavailable = (e) => {
                    chuncks.push(e.data);
                };
                mediaRecorder.start();
            });


        }
    );
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if(request.action == "start"){
        startMonitoring();
    }
});