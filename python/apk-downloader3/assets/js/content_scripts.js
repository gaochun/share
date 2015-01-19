/** Evozi www.evozi.com **/
"use strict";

var addDownloadButton = function(container, packageName) {
    var button = document.createElement("span");
    button.className = 'apps medium play-button';
        var btn = document.createElement('button');
            var span = document.createElement('span');
            span.appendChild(document.createTextNode('Download APK'));
        btn.appendChild(span);
    button.appendChild(btn);

    button.addEventListener("click", function(e) {
        e.preventDefault();

        var elmLatestVersion = document.querySelector("div.id-review-version-filter div.dropdown-menu-children div:nth-child(2)");
        var versionCode = elmLatestVersion ? elmLatestVersion.getAttribute("data-dropdown-value") : 0;

        var data = {
            packageName: packageName,
            versionCode: versionCode
        };

        BrowserMessage.sendMessage({
            cmd: "download",
            data: data
        }, function(resp) {

        });
    });

    container.appendChild(button);
    button.click();
}

var findInstallButton = function(node) {
    var buttonContainer = node.querySelector("span.buy-button-container.apps");
    if (!buttonContainer) {
        buttonContainer = node.querySelector("span.price.buy.id-track-click");
        if (!buttonContainer) {
            return false;
        }
    }

    var metaPrice = buttonContainer.querySelector("meta[itemprop='price']");
    if (metaPrice && metaPrice.getAttribute("content") == 0) {
        var packageName = buttonContainer.getAttribute("data-docid");
        addDownloadButton(buttonContainer.parentNode, packageName);
    }
}

var observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.addedNodes.length > 0) {
            for (var i = 0, size = mutation.addedNodes.length; i < size; i++) {
                var node = mutation.addedNodes[i];
                // find reviews section
                if (node.nodeType === 1 && node.tagName === "DIV" && node.classList && node.hasAttribute("data-docid")) {
                    var classList = node.classList;
                    if (classList.contains("details-wrapper") && classList.contains("apps") && !classList.contains("square-cover")) {
                        findInstallButton(document.querySelector("div.details-actions"));
                        break;
                    }
                }
            }
        }
    });
});

var ERROR_MESSAGES = {
    "-1": "Cannot download. Please make sure your email and device ID are correct.",
    "-2": "Cannot download this app.",
};

BrowserMessage.addMessageListener(function(message, sender, sendResponse) {
    if (message.cmd === 'downloadResponse') {
        if (message.error < 0) {
            alert(ERROR_MESSAGES[message.error.toString()])
        }
    }
});

observer.observe(document.getElementById("wrapper"), { attributes: false, childList: true, characterData: false, subtree: true });
findInstallButton(document.querySelector("div.details-actions"));
/** Evozi www.evozi.com **/