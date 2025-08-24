# Vinted Token Extractor - Firefox Browser Extension

## Overview

This Firefox browser extension automatically extracts Vinted authentication tokens from the browser and pre-fills the token injection form on your Django application. No more manual copying and pasting of long token strings!

## Features

- 🚀 One-click token extraction from Vinted.be
- 🔒 Secure cookie access with proper permissions
- 🎯 Direct navigation to pre-filled injection form
- 🖥️ Clean, minimal UI
- ⚡ Instant token transfer to your local application

## Installation Instructions

### Step 1: Create Extension Directory
```bash
mkdir vinted-token-extractor
cd vinted-token-extractor
```

### Step 2: Create Extension Files

Create the following files in your extension directory:

## Files Structure
```
vinted-token-extractor/
├── manifest.json
├── background.js
├── content.js
├── popup.html
├── popup.js
├── popup.css
└── icons/
    ├── icon-16.png
    ├── icon-32.png
    ├── icon-48.png
    └── icon-128.png
```

---

## File Contents

### 1. manifest.json
```json
{
  "manifest_version": 2,
  "name": "Vinted Token Extractor",
  "version": "1.0.0",
  "description": "Extract Vinted authentication tokens and auto-fill your price watch application",
  
  "permissions": [
    "cookies",
    "tabs",
    "activeTab",
    "*://*.vinted.be/*",
    "*://*.vinted.fr/*",
    "*://*.vinted.com/*",
    "*://*.vinted.nl/*",
    "*://*.vinted.es/*",
    "*://*.vinted.it/*",
    "*://*.vinted.de/*",
    "*://*.vinted.at/*",
    "*://*.vinted.cz/*",
    "*://*.vinted.sk/*",
    "*://*.vinted.hu/*",
    "*://*.vinted.pl/*",
    "*://*.vinted.lt/*",
    "*://*.vinted.lv/*",
    "*://*.vinted.ee/*",
    "http://localhost:8000/*"
  ],
  
  "background": {
    "scripts": ["background.js"],
    "persistent": false
  },
  
  "content_scripts": [
    {
      "matches": [
        "*://*.vinted.be/*",
        "*://*.vinted.fr/*",
        "*://*.vinted.com/*",
        "*://*.vinted.nl/*",
        "*://*.vinted.es/*",
        "*://*.vinted.it/*",
        "*://*.vinted.de/*",
        "*://*.vinted.at/*",
        "*://*.vinted.cz/*",
        "*://*.vinted.sk/*",
        "*://*.vinted.hu/*",
        "*://*.vinted.pl/*",
        "*://*.vinted.lt/*",
        "*://*.vinted.lv/*",
        "*://*.vinted.ee/*"
      ],
      "js": ["content.js"],
      "run_at": "document_idle"
    }
  ],
  
  "browser_action": {
    "default_popup": "popup.html",
    "default_title": "Extract Vinted Tokens",
    "default_icon": {
      "16": "icons/icon-16.png",
      "32": "icons/icon-32.png",
      "48": "icons/icon-48.png",
      "128": "icons/icon-128.png"
    }
  },
  
  "icons": {
    "16": "icons/icon-16.png",
    "32": "icons/icon-32.png",
    "48": "icons/icon-48.png",
    "128": "icons/icon-128.png"
  },
  
  "web_accessible_resources": [
    "popup.html"
  ]
}
```

### 2. background.js
```javascript
// Background script for handling extension logic
console.log('Vinted Token Extractor: Background script loaded');

// Listen for messages from content script or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extractTokens') {
    extractTokensAndRedirect(sender.tab);
  } else if (request.action === 'getTokens') {
    getTokensFromCookies(sendResponse);
    return true; // Will respond asynchronously
  }
});

// Function to extract tokens and redirect
async function extractTokensAndRedirect(tab) {
  try {
    console.log('Extracting tokens from tab:', tab.url);
    
    // Get cookies from the current Vinted domain
    const url = new URL(tab.url);
    const domain = url.hostname;
    
    // Extract access token
    const accessTokenCookie = await new Promise((resolve) => {
      chrome.cookies.get({
        url: tab.url,
        name: 'access_token_web'
      }, resolve);
    });
    
    // Extract session token
    const sessionTokenCookie = await new Promise((resolve) => {
      chrome.cookies.get({
        url: tab.url,
        name: '_vinted_fr_session'
      }, resolve);
    });
    
    console.log('Access token found:', !!accessTokenCookie);
    console.log('Session token found:', !!sessionTokenCookie);
    
    if (!accessTokenCookie || !sessionTokenCookie) {
      // Show error popup or notification
      chrome.tabs.executeScript(tab.id, {
        code: `
          alert('❌ Tokens not found!\\n\\nPlease make sure you are logged into Vinted and try again.\\n\\nRequired cookies:\\n- access_token_web\\n- _vinted_fr_session');
        `
      });
      return;
    }
    
    // Build the pre-filled URL
    const accessToken = encodeURIComponent(accessTokenCookie.value);
    const sessionToken = encodeURIComponent(sessionTokenCookie.value);
    const targetUrl = `http://localhost:8000/token/inject/?access_token=${accessToken}&session_token=${sessionToken}`;
    
    console.log('Opening target URL with pre-filled tokens');
    
    // Open new tab with pre-filled form
    chrome.tabs.create({
      url: targetUrl,
      active: true
    });
    
    // Show success notification
    chrome.tabs.executeScript(tab.id, {
      code: `
        // Create a temporary success notification
        const notification = document.createElement('div');
        notification.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #10B981; color: white; padding: 16px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 9999; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 300px;';
        notification.innerHTML = '🎉 <strong>Tokens Extracted!</strong><br>Opening injection form in new tab...';
        document.body.appendChild(notification);
        
        // Remove notification after 3 seconds
        setTimeout(() => {
          if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
          }
        }, 3000);
      `
    });
    
  } catch (error) {
    console.error('Error extracting tokens:', error);
    
    // Show error notification
    chrome.tabs.executeScript(tab.id, {
      code: `
        alert('❌ Error extracting tokens: ${error.message}\\n\\nPlease try again or extract tokens manually.');
      `
    });
  }
}

// Function to get tokens for popup display
async function getTokensFromCookies(sendResponse) {
  try {
    // Get current active tab
    const tabs = await new Promise((resolve) => {
      chrome.tabs.query({ active: true, currentWindow: true }, resolve);
    });
    
    if (!tabs[0] || !tabs[0].url.includes('vinted.')) {
      sendResponse({ error: 'Not on a Vinted page' });
      return;
    }
    
    const tab = tabs[0];
    
    // Get cookies
    const accessTokenCookie = await new Promise((resolve) => {
      chrome.cookies.get({
        url: tab.url,
        name: 'access_token_web'
      }, resolve);
    });
    
    const sessionTokenCookie = await new Promise((resolve) => {
      chrome.cookies.get({
        url: tab.url,
        name: '_vinted_fr_session'
      }, resolve);
    });
    
    sendResponse({
      accessToken: accessTokenCookie?.value,
      sessionToken: sessionTokenCookie?.value,
      domain: new URL(tab.url).hostname
    });
    
  } catch (error) {
    console.error('Error getting tokens:', error);
    sendResponse({ error: error.message });
  }
}
```

### 3. content.js
```javascript
// Content script for Vinted pages
console.log('Vinted Token Extractor: Content script loaded on', window.location.hostname);

// Add visual indicator that extension is active
function addExtensionIndicator() {
  // Only add if not already present
  if (document.getElementById('vinted-token-extractor-indicator')) {
    return;
  }
  
  const indicator = document.createElement('div');
  indicator.id = 'vinted-token-extractor-indicator';
  indicator.style.cssText = `
    position: fixed;
    bottom: 20px;
    left: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 8px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    z-index: 9999;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    opacity: 0.8;
    transition: opacity 0.3s ease;
  `;
  indicator.innerHTML = '🔧 Token Extractor Ready';
  
  // Add hover effect
  indicator.addEventListener('mouseenter', () => {
    indicator.style.opacity = '1';
    indicator.innerHTML = '🔧 Click extension icon to extract tokens';
  });
  
  indicator.addEventListener('mouseleave', () => {
    indicator.style.opacity = '0.8';
    indicator.innerHTML = '🔧 Token Extractor Ready';
  });
  
  document.body.appendChild(indicator);
  
  // Remove indicator after 5 seconds
  setTimeout(() => {
    if (indicator.parentNode) {
      indicator.style.transition = 'opacity 0.5s ease';
      indicator.style.opacity = '0';
      setTimeout(() => {
        if (indicator.parentNode) {
          indicator.parentNode.removeChild(indicator);
        }
      }, 500);
    }
  }, 5000);
}

// Add indicator when page loads
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', addExtensionIndicator);
} else {
  addExtensionIndicator();
}

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'checkTokens') {
    // This could be used for additional checks if needed
    sendResponse({ status: 'ready' });
  }
});
```

### 4. popup.html
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {
      margin: 0;
      padding: 0;
      width: 320px;
      min-height: 200px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }
    
    .container {
      padding: 20px;
    }
    
    .header {
      text-align: center;
      margin-bottom: 20px;
    }
    
    .header h1 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
    }
    
    .header p {
      margin: 5px 0 0;
      font-size: 12px;
      opacity: 0.9;
    }
    
    .status {
      background: rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      padding: 12px;
      margin-bottom: 15px;
      font-size: 12px;
    }
    
    .status-item {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
    }
    
    .status-item:last-child {
      margin-bottom: 0;
    }
    
    .status-good {
      color: #10B981;
    }
    
    .status-bad {
      color: #F87171;
    }
    
    .extract-btn {
      width: 100%;
      background: rgba(255, 255, 255, 0.2);
      border: 1px solid rgba(255, 255, 255, 0.3);
      color: white;
      padding: 12px 16px;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
      margin-bottom: 10px;
    }
    
    .extract-btn:hover {
      background: rgba(255, 255, 255, 0.3);
      transform: translateY(-1px);
    }
    
    .extract-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none;
    }
    
    .footer {
      text-align: center;
      font-size: 10px;
      opacity: 0.7;
    }
    
    .loading {
      text-align: center;
      padding: 20px;
    }
    
    .spinner {
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-radius: 50%;
      border-top: 2px solid white;
      width: 20px;
      height: 20px;
      animation: spin 1s linear infinite;
      margin: 0 auto 10px;
    }
    
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🔧 Token Extractor</h1>
      <p>Extract Vinted authentication tokens</p>
    </div>
    
    <div id="loading" class="loading">
      <div class="spinner"></div>
      <p>Checking page...</p>
    </div>
    
    <div id="content" style="display: none;">
      <div class="status" id="status">
        <!-- Status will be populated by JavaScript -->
      </div>
      
      <button id="extractBtn" class="extract-btn">
        🚀 Extract Tokens & Open Form
      </button>
      
      <div class="footer">
        <p>Make sure you're logged into Vinted</p>
      </div>
    </div>
  </div>
  
  <script src="popup.js"></script>
</body>
</html>
```

### 5. popup.js
```javascript
document.addEventListener('DOMContentLoaded', async () => {
  const loadingDiv = document.getElementById('loading');
  const contentDiv = document.getElementById('content');
  const statusDiv = document.getElementById('status');
  const extractBtn = document.getElementById('extractBtn');
  
  try {
    // Check if we're on a Vinted page
    const tabs = await new Promise((resolve) => {
      chrome.tabs.query({ active: true, currentWindow: true }, resolve);
    });
    
    const currentTab = tabs[0];
    
    if (!currentTab || !currentTab.url.includes('vinted.')) {
      showError('❌ Not on a Vinted page', 'Please navigate to vinted.be or another Vinted domain first.');
      return;
    }
    
    // Get token status
    chrome.runtime.sendMessage({ action: 'getTokens' }, (response) => {
      loadingDiv.style.display = 'none';
      contentDiv.style.display = 'block';
      
      if (response.error) {
        showError('❌ Error checking tokens', response.error);
        return;
      }
      
      // Update status display
      const hasAccess = !!response.accessToken;
      const hasSession = !!response.sessionToken;
      
      statusDiv.innerHTML = `
        <div class="status-item">
          <span>Access Token:</span>
          <span class="${hasAccess ? 'status-good' : 'status-bad'}">
            ${hasAccess ? '✅ Found' : '❌ Missing'}
          </span>
        </div>
        <div class="status-item">
          <span>Session Token:</span>
          <span class="${hasSession ? 'status-good' : 'status-bad'}">
            ${hasSession ? '✅ Found' : '❌ Missing'}
          </span>
        </div>
        <div class="status-item">
          <span>Domain:</span>
          <span>${response.domain || 'Unknown'}</span>
        </div>
      `;
      
      // Update button state
      if (hasAccess && hasSession) {
        extractBtn.textContent = '🚀 Extract Tokens & Open Form';
        extractBtn.disabled = false;
      } else {
        extractBtn.textContent = '❌ Tokens Missing - Please Login';
        extractBtn.disabled = true;
      }
    });
    
  } catch (error) {
    console.error('Popup error:', error);
    showError('❌ Extension Error', error.message);
  }
  
  // Handle extract button click
  extractBtn.addEventListener('click', () => {
    extractBtn.textContent = '🔄 Extracting...';
    extractBtn.disabled = true;
    
    chrome.runtime.sendMessage({ action: 'extractTokens' });
    
    // Close popup after a short delay
    setTimeout(() => {
      window.close();
    }, 1000);
  });
  
  function showError(title, message) {
    loadingDiv.style.display = 'none';
    contentDiv.innerHTML = `
      <div class="status">
        <div style="text-align: center;">
          <h3 style="margin: 0 0 10px; color: #F87171;">${title}</h3>
          <p style="margin: 0; font-size: 12px; opacity: 0.9;">${message}</p>
        </div>
      </div>
    `;
    contentDiv.style.display = 'block';
  }
});
```

### 6. Icons

You'll need to create icon files in the `icons/` directory. You can use any image editor to create simple 16x16, 32x32, 48x48, and 128x128 pixel PNG icons. 

For a quick solution, you can create simple text-based icons or use online icon generators. The icons should be:
- **icon-16.png** (16x16 pixels)
- **icon-32.png** (32x32 pixels) 
- **icon-48.png** (48x48 pixels)
- **icon-128.png** (128x128 pixels)

**Simple Icon Design Ideas:**
- Blue/purple background with "VT" text (Vinted Token)
- Cookie icon with a "V" 
- Key/lock icon with Vinted colors

---

## Installation in Firefox

### Method 1: Temporary Installation (Development)

1. **Open Firefox Developer Tools**
   - Navigate to `about:debugging`
   - Click "This Firefox" in the sidebar

2. **Load Extension**
   - Click "Load Temporary Add-on"
   - Select the `manifest.json` file from your extension directory
   - The extension will be loaded temporarily

### Method 2: Permanent Installation (Signing Required)

For permanent installation, you would need to:
1. Package the extension as a `.xpi` file
2. Submit to Mozilla Add-ons for signing (free)
3. Install the signed `.xpi` file

For development purposes, Method 1 (temporary) is sufficient.

---

## Usage Instructions

### 1. Setup Your Local Application
Make sure your Django application is running on `http://localhost:8000`

### 2. Login to Vinted
- Navigate to `https://www.vinted.be` (or your preferred Vinted domain)
- Login to your account to ensure authentication cookies are set

### 3. Extract Tokens
- Click the extension icon in Firefox toolbar
- Check that both tokens show "✅ Found" status
- Click "🚀 Extract Tokens & Open Form"
- A new tab will open with pre-filled token fields

### 4. Complete Injection
- Choose your expiration preference (timed or never expire)
- Click "💉 Inject Token"
- Your tokens are now active in the application!

---

## Configuration

### Changing Target URL

If your Django application runs on a different port or domain, update the target URL in `background.js`:

```javascript
// Change this line in background.js
const targetUrl = `http://localhost:8000/token/inject/?access_token=${accessToken}&session_token=${sessionToken}`;

// To your custom URL:
const targetUrl = `http://your-domain.com:PORT/token/inject/?access_token=${accessToken}&session_token=${sessionToken}`;
```

### Adding More Vinted Domains

To support additional Vinted domains, add them to the `permissions` and `content_scripts.matches` arrays in `manifest.json`.

---

## Security Considerations

1. **Cookie Access**: The extension only accesses cookies on Vinted domains
2. **Local Communication**: Tokens are only sent to localhost (your local development environment)
3. **No Storage**: Tokens are not stored by the extension - they're immediately passed to your application
4. **Permissions**: Minimal required permissions for functionality

---

## Troubleshooting

### "Tokens not found" Error
- Ensure you're logged into Vinted
- Clear browser cache and cookies, then login again
- Check if you're on the correct Vinted domain

### "Not on a Vinted page" Error
- Make sure you're on a page that contains "vinted" in the URL
- Try refreshing the Vinted page

### Extension not visible
- Check that it was loaded successfully in `about:debugging`
- Look for any error messages in the browser console

### Pre-filled form not working
- Verify your Django application is running on the expected URL
- Check browser console for any JavaScript errors
- Ensure the Django view modifications were applied correctly

---

## Development Tips

### Testing the Extension
1. Load extension temporarily in Firefox
2. Navigate to Vinted and login
3. Open browser console to see extension logs
4. Click extension icon and check functionality

### Debugging
- Use `console.log()` statements in the extension scripts
- Check browser console in both the Vinted page and popup
- Monitor network requests in Developer Tools

### Modifying the Extension
- After making changes, reload the extension in `about:debugging`
- Clear browser cache if changes don't take effect
- Test each component individually

---

## Future Enhancements

Possible improvements to consider:
- Support for other browsers (Chrome, Edge)
- Token validation before extraction
- Settings page for custom target URLs
- Automatic token refresh notifications
- Support for multiple price watch instances

---

This extension streamlines the token injection process from a tedious manual task to a single click operation! 🚀