chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'getPageUrl') {
    sendResponse({ url: window.location.href });
  } else if (message.action === 'highlightFakeImages') {
    highlightFakeImages(message.fakeImages);
  }
});

function highlightFakeImages(fakeImages) {
  try {
    const images = document.querySelectorAll('img');
    const fakeImageUrls = fakeImages.map(img => img.url);

    images.forEach(img => {
      if (fakeImageUrls.includes(img.src)) {
        img.style.border = '5px solid red';
        img.style.position = 'relative';
        const overlay = document.createElement('div');
        overlay.style.position = 'absolute';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.width = '100%';
        overlay.style.height = '100%';
        overlay.style.backgroundColor = 'rgba(255, 0, 0, 0.3)';
        img.parentElement.style.position = 'relative';
        img.parentElement.appendChild(overlay);
      }
    });
  } catch (error) {
    console.error('Error highlighting fake images:', error);
  }
}
