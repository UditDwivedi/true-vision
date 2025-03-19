const pop_up = () => [0, 1].forEach(e => covers[e].classList.toggle("hidden"));
const about_us = () => [0, 2].forEach(e => covers[e].classList.toggle("hidden"));

const closeAll = () => {
    covers.forEach(e => e.classList.add("hidden"));

    setTimeout(() => {
        fileName.textContent = '';

        displays.forEach(e => e.classList.remove("display-show"));

        ["output", "confidence"].forEach(e => {
            document.getElementById(e).classList.add("d-none");
        });
        
        actionBtn.innerHTML = "Select";
        actionBtn.htmlFor = "video";

        anotherBtn.classList.add("d-none");
    }, 200);
}

const changeAction = () => {
    if (vid.files.length > 0) {
        const file = vid.files[0];

        if (file.name.endsWith("mp4")) {
            displays[0].src = URL.createObjectURL(file);
            displays[0].classList.add("display-show");
            displays[0].load(); displays[0].play();
        } else {
            displays[1].src = URL.createObjectURL(file);
            displays[1].classList.add("display-show");
        }
        
        fileName.textContent = `File Name: ${file.name}`;
        
        actionBtn.innerHTML = "Check for DeepFake";
        actionBtn.htmlFor = '';
        actionBtn.onclick = () => testForFile(file); 
    }
}

const testForFile = file => {
    const data = new FormData(); data.append("video", file);
    const loader = document.getElementById("loader-holder");

    loader.classList.remove("hidden");
    
    fetch('/api', {
        method: 'POST', body: data
    })
    .then(res => res.json())
    .then(data => {
        ["output", "confidence"].forEach(e => {
            const elem = document.getElementById(e);
            
            elem.querySelector("label").innerHTML = data[e]; 
            elem.classList.remove("d-none");
        });

        actionBtn.innerHTML = "Generate Report";
        
        anotherBtn.classList.remove("d-none");
    })
    .finally(() => {
        loader.classList.add("hidden");
    });
}

const covers = Array.from(document.getElementsByClassName("cover"));

const vid = document.getElementById("video");
const displays = Array.from(document.getElementsByClassName("display"));

const fileName = document.getElementById("fileName");
const actionBtn = document.getElementById("action-btn");

const anotherBtn = document.getElementById("another-btn");