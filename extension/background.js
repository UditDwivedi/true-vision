chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'scrapeContent') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tabId = tabs[0]?.id;
      if (tabId) {
        chrome.scripting.executeScript(
          {
            target: { tabId: tabId },
            files: ['content.js']
          },
          () => {
            chrome.tabs.sendMessage(tabId, { action: 'getPageUrl' }, async (response) => {
              if (chrome.runtime.lastError) {
                console.error(`Message sending failed: ${chrome.runtime.lastError.message}`);
                sendResponse({ result: 'Error occurred during message sending' });
                return;
              }
              const pageUrl = response?.url;
              if (pageUrl) {
                try {
                  const result = await fetch('http://localhost:3000/scrape', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: pageUrl })
                  });

                  if (!result.ok) {
                    throw new Error('Failed to scrape content');
                  }

                  const json = await result.json();
                  console.log('Scraping result:', json);
                  sendResponse({
                    result: json.message,
                    csvFile: json.csv_file,
                    fakeImages: json.fakeImages // Ensure server returns fakeImages
                  });
                } catch (error) {
                  console.error('Scraping error:', error);
                  sendResponse({ result: 'Error occurred during scraping' });
                }
              } else {
                console.error('Failed to get page URL');
                sendResponse({ result: 'Failed to get page URL' });
              }
            });
          }
        );
      } else {
        console.error('Tab ID is undefined');
        sendResponse({ result: 'Tab ID is undefined' });
      }
    });
    return true; // Keep the message channel open
  }
});
