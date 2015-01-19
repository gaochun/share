/** Evozi www.evozi.com **/
"use strict";

var BrowserMessage = new function() {
    var EXTENSION_ID = chrome.i18n.getMessage("@@extension_id");

    var sendMessage = function(message, callback) {
        chrome.runtime.sendMessage(message, callback);
    }

    var addMessageListener = function(fn) {
        chrome.runtime.onMessage.addListener(fn);
    }

    this.sendMessage = sendMessage;
    this.addMessageListener = addMessageListener;
}

var BrowserStorage = new function() {
    var STORAGE = chrome.storage.local;
    
    var get = function(field, callback) {
        STORAGE.get(field, callback);
    }
    
    var set = function(data, callback) {
        STORAGE.set(data, callback);
    }
    
    var remove = function(data, callback) {
        STORAGE.remove(data, callback);
    }

    var clear = function() {
        STORAGE.clear();
    }
    
    this.get = get;
    this.set = set;
    this.remove = remove;
}

var BrowserCookie = new function() {
    var get = function(details, callback) {
        chrome.cookies.get(details, callback);
    }

    var set = function(details, callback) {
        if (details.name === "MarketDA") {  // fix Failed - Server problem error
            chrome.cookies.set({
                url: details.url,
                name: details.name,
                value: details.value,
                path: "/",
                domain: ".android.clients.google.com",
                secure: false
            }, callback);
        } else {
            chrome.cookies.set(details, callback);
        }
    }    

    var remove = function(details, callback) {
        chrome.cookies.remove(details, callback);
    }

    this.get = get;
    this.set = set;
    this.remove = remove;
}

var BrowserApi = new function() {
    var API_URL = "https://android.clients.google.com/market/api/ApiRequest";

    var getDataString = function(data) {
        var str = "";
        for (var key in data) {
            str += key + "=" + encodeURIComponent(data[key]) + "&";
        }

        if (str.length > 0) {
            str = str.substr(0, str.length - 1);
        }
        return str;
    }

    var get = function(url, data, onload, onerror) {

    }

    var post = function(data, onload, onerror) {
        var xhr = new XMLHttpRequest();
        xhr.responseType = "arraybuffer";
        xhr.open("POST", API_URL);
        xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        xhr.onload = function(e) {
            onload.call(null, xhr);
        }

        xhr.send(getDataString(data));
    }

    this.get = get;
    this.post = post;
}

var BrowserDownloads = new function() {
    var download = function(url, filename) {
        chrome.downloads.download({
            url: url,
            filename: filename
        });
    }

    this.download = download;
}

var BrowserTabs = new function() {
    var create = function(options) {
        chrome.tabs.create(options);
    }

    var sendMessage = function(tabId, message, callback) {
        chrome.tabs.sendMessage(tabId, message, callback);
    }

    this.create = create;
    this.sendMessage = sendMessage;
}

var BrowserGzip = new function() {
    var uncompress = function(ua) {
        return (new JXG.Util.Unzip(ua)).unzip()[0][0];
    }

    this.uncompress = uncompress;
}