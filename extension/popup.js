document.addEventListener('DOMContentLoaded', () => {
  const scrapeButton = document.getElementById('scrapeButton');
  const statusDiv = document.getElementById('status');

  if (scrapeButton) {
    scrapeButton.addEventListener('click', () => {
      chrome.runtime.sendMessage({ action: 'scrapeContent' }, (response) => {
        if (chrome.runtime.lastError) {
          console.error(`Background script error: ${chrome.runtime.lastError.message}`);
          statusDiv.textContent = 'Status: Error occurred';
        } else {
          console.log('Background script response:', response);
          statusDiv.textContent = 'Status: ' + (response?.result || 'Unknown result');
          if (response.fakeImages) {
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
              const tabId = tabs[0]?.id;
              if (tabId) {
                chrome.tabs.sendMessage(tabId, { action: 'highlightFakeImages', fakeImages: response.fakeImages });
              }
            });
          }
        }
      });
    });
  } else {
    console.error('Scrape button not found');
  }
});
