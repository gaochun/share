/** Evozi www.evozi.com **/
"use strict";

function hasValidSession(callback) {
    var authToken = localStorage.getItem("authToken");
    if (authToken == null) {
        callback(false);
        return;
    }

    if (1) {
        callback(true);
        return;
    }

    var xhr = new XMLHttpRequest();
    xhr.open("GET", FDFE_URL_BASE + "delivery");
    /* GoogleLogin auth=... is required, otherwise you get a 302 which is
     * uncatchable */
    xhr.setRequestHeader("Authorization", "GoogleLogin auth=" + authToken);
    xhr.onload = function () {
        console.log("xhr status " + xhr.status);
        if (xhr.status == 401) {
            /* 401 Unauthorized: invalid login token */
            localStorage.removeItem("authToken");
            callback(false);
        } else {
            /* assume valid session for other status codes (400, ???) */
            callback(true);
        }
    };
    xhr.onerror = function () {
        console.log("Unable to test session for validity, assuming valid one");
        callback(true);
    };
    xhr.send(null);
}


chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (request.cmd === 'download') {
        MarketSession.download(request.data.packageName, request.data.versionCode, sender.tab.id);
    }
});

chrome.runtime.onInstalled.addListener(function(details) {
    if (details.reason === "update") {
        chrome.tabs.create({
            url: "http://apps.evozi.com/apk-downloader/"
        });
    } else if(details.reason == "install"){
    	chrome.tabs.create({url: "options.html"});
    }
});

var _gaq = _gaq || [];
_gaq.push(["_setAccount", "UA-33205486-2"]);
_gaq.push(['_trackPageview']);

(function() {
  var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
  ga.src = 'https://ssl.google-analytics.com/ga.js';
  var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
})();


/* Try to focus existing options page or open a new tab for it */
function openTab(url) {
    chrome.tabs.query({
        url: url
    }, function(tabs) {
        if (tabs.length > 0) {
            focusTab(tabs[0]);
        } else {
            chrome.tabs.create({
                url: url,
                active: true
            }, focusTab);
        }

        function focusTab(tab) {
            chrome.windows.update(tab.windowId, {
                focused: true
            });
        }
    });
}
