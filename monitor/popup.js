document.addEventListener('DOMContentLoaded', () => {
    const startbutton = document.getElementById("start");   
    const stopbutton = document.getElementById("stop");

    let monitoring = false;

    const start = () => {
        startbutton.disabled = true;
        stopbutton.disabled = false;
        monitoring = true;
        chrome.runtime.sendMessage({ action: "start" });
    };
    const stop = () => {
        startbutton.disabled = false;
        stopbutton.disabled = true;
        monitoring = false;
        chrome.runtime.sendMessage({ action: "stop" });
    };

    startbutton.addEventListener('click', start);
    stopbutton.addEventListener('click', stop);
});