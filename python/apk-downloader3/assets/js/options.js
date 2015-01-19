/** Evozi www.evozi.com **/
"use strict";

var Options = new function() {
    var DEFAULT_SIM_SETTINGS = {
        country: "USA",
        operator: "T-Mobile",
        operatorCode: "31020"
    };

    var formInfo, formLogin, formDevice,
        txtAuthEmail, txtDeviceId,
        inpEmail, inpPassword, inpDeviceId, inpLocale, inpCountryCode, inpDeviceAndSdkVersion, 
        sltCountry, sltOperator,
        btnDefault, btnDeviceDefault, btnDeviceSave, btnLogin, btnLogout, 
        btnAdv, btnSave;

    /**
     * ClientLogin errors, taken from
     * https://developers.google.com/accounts/docs/AuthForInstalledApps
     */
    var clientLoginErrors = {
        "BadAuthentication": "Incorrect username or password.",
        "NotVerified": "The account email address has not been verified. You need to access your Google account directly to resolve the issue before logging in here.",
        "TermsNotAgreed": "You have not yet agreed to Google's terms, acccess your Google account directly to resolve the issue before logging in using here.",
        "CaptchaRequired": "A CAPTCHA is required. (not supported, try logging in another tab)",
        "Unknown": "Unknown or unspecified error; the request contained invalid input or was malformed.",
        "AccountDeleted": "The user account has been deleted.",
        "AccountDisabled": "The user account has been disabled.",
        "ServiceDisabled": "Your access to the specified service has been disabled. (The user account may still be valid.)",
        "ServiceUnavailable": "The service is not available; try again later."
    };

    var clearData = function(callback) {
        BrowserStorage.remove(["account", "sim"], callback);
    }

    var saveAuth = function(data, callback) {
        BrowserStorage.set({
            account: data,
            sim: DEFAULT_SIM_SETTINGS
        }, callback);
    }

    var getAccountSettings = function(callback) {
        BrowserStorage.get(["sim", "account"], function(items) {
            if (!items.sims) {
                setSimSettings(DEFAULT_SIM_SETTINGS);
                items.sim = DEFAULT_SIM_SETTINGS;
            }

            callback.call(null, items);
        });
    }

    var setSimSettings = function(sim, callback) {
        BrowserStorage.set({
            sim: sim
        }, callback);
    };

    var refreshViews = function() {
        getAccountSettings(function(items) {
            if (!items.account) {
                inpEmail.value = "";
                inpPassword.value = "";
                inpDeviceId.value = "";

                txtAuthEmail.value = "";
                txtDeviceId.value = "";
                formLogin.style.display = "block";
                formInfo.style.display = "none";
                formDevice.style.display = "none";
            } else {
                txtAuthEmail.value = items.account.email;
                txtDeviceId.value = items.account.deviceId.toUpperCase();

                formInfo.style.display = "block";
                formLogin.style.display = "none";
                formDevice.style.display = "block";

                //checkSimSettings();
                //initCountryOptions();
            }
        });
    };

    var login = function(email, password, deviceId) {
        var ACCOUNT_TYPE_HOSTED_OR_GOOGLE = "HOSTED_OR_GOOGLE";
        var URL_LOGIN = "https://www.google.com/accounts/ClientLogin";
        var LOGIN_SERVICE = "androidsecure";

        var params = {
            "Email": email,
            "Passwd": password,
            "service": LOGIN_SERVICE,
            "accountType": ACCOUNT_TYPE_HOSTED_OR_GOOGLE
        };

        var xhr = new XMLHttpRequest();
        xhr.open("POST", URL_LOGIN, true);

        var paramsStr = "";
        for (var key in params) {
            paramsStr += "&" + key + "=" + encodeURIComponent(params[key])
        }

        xhr.onload = function() {
            var AUTH_TOKEN = "";
            var response = xhr.responseText;

            var error = response.match(/Error=(\w+)/);
            if (error) {
                var msg = clientLoginErrors[error[1]] || error[1];
                alert("Authentication failed, please make sure you enter a valid email and password, if you have 2 step auth set up, please use application specified password to login.\n" + msg);
                return;
            }

            var match = response.match(/Auth=([a-z0-9=_\-]+)/i);
            if (match) {
                AUTH_TOKEN = match[1];
            }

            if (!AUTH_TOKEN) {
                // should never happen...
                alert("ERROR: Authentication token not available, cannot login.");
                return;
            }

            saveAuth({
                email: email,
                authToken: AUTH_TOKEN,
                deviceId: deviceId
            }, refreshViews);
        };

        xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        xhr.send(paramsStr);
    };

    var initForm = function() {
        formInfo = document.getElementById("info_form");
        formDevice = document.getElementById("device_form");
        formLogin = document.getElementById("login_form");

        txtAuthEmail = document.getElementById("auth_email");
        txtDeviceId = document.getElementById("device_id");

        inpEmail = document.getElementById("user_email");
        inpEmail.addEventListener("blur", function(e) {
            if (inpEmail.value.length > 0 && inpEmail.value.indexOf("@") === -1) {
                inpEmail.value = inpEmail.value + "@gmail.com";
            }
        });
        inpPassword = document.getElementById("user_password");
        inpDeviceId = document.getElementById("user_device_id");

        sltCountry = document.getElementById("slt_country");
        sltOperator = document.getElementById("slt_operator");
        btnDefault = document.getElementById("btn_default");
        btnDeviceDefault = document.getElementById("btn_device_default");

        inpLocale = document.getElementById("device_locale");
        inpCountryCode = document.getElementById("country_code");
        inpDeviceAndSdkVersion = document.getElementById("deviceAndSdkVersion");

        var btnsAdv = document.getElementsByClassName("btn-advanced-settings");
        function toggleAdvCb(e) {
            e.preventDefault();
            formInfo.classList.toggle("hide-advanced");
            formInfo.classList.toggle("show-advanced");
        }
        for (var i=0; i<btnsAdv.length; i++) {
            btnsAdv[i].addEventListener("click", toggleAdvCb);
        }

        var btnsDevice = document.getElementsByClassName("btn-device-settings");

        for (var i=0; i<btnsDevice.length; i++) {
                btnsDevice[i].addEventListener("click", function (e) {
                e.preventDefault();
                formDevice.classList.toggle("hide-device");
                formDevice.classList.toggle("show-device");
            });
        }


        btnDefault.onclick = function(e) {
            e.preventDefault();
            if (confirm('Reset to default sim operator?')) {
                resetSimSettings();
                initCountryOptions();
            }
        };

        btnDeviceDefault.onclick = function(e) {
            e.preventDefault();
            if (confirm('Reset to default device info?')) {
                resetDeviceSettings();
                refreshViews();
            }
        };

        btnSave = document.getElementById("btn_save");
        btnSave.onclick = function(e) {
            e.preventDefault();
            var country = sltCountry.value;
            var operator = sltOperator.value;
            var operatorCode = codes[country][operator];
            setSimSettings({
                country: country,
                operator: operator,
                operatorCode: operatorCode
            });
            alert('Successfully Saved!');
        };

        btnDeviceSave = document.getElementById("btn_device_save");
        btnDeviceSave.onclick = function(e) {
            e.preventDefault();
            var locale = inpLocale.value;
            var countryCode = inpCountryCode.value;
            var deviceAndSdkVersion = inpDeviceAndSdkVersion.value;
            
            setDeviceSettings({
                locale: locale,
                countryCode: countryCode,
                deviceAndSdkVersion: deviceAndSdkVersion
            });
            alert('Device Info Successfully Saved!');
        };



        btnLogin = document.getElementById("btn_login");
        btnLogin.addEventListener("click", function(e) {
            e.preventDefault();

            var email = inpEmail.value;
            var password = inpPassword.value;
            var deviceId = inpDeviceId.value;

            var match = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/.exec(email);
            if (!match) {
                $('#error_notification').removeClass('hidden').addClass('show');
                $('#error_text').text("Please enter valid email!");
                inpEmail.focus();
                return;
            }

            if (password.length == 0) {
                $('#error_notification').removeClass('hidden').addClass('show');
                $('#error_text').text("Please enter a password!");
                inpPassword.focus();
                return;
            }

            if (!/^[0-9a-f]{16}$/i.test(deviceId)) {
                $('#error_notification').removeClass('hidden').addClass('show');
                $('#error_text').text("Android Device ID (GSF ID) must be 16 characters long and only contains characters from 0-9, A-F");
                inpDeviceId.focus();
                return;
            }

            login(email, password, deviceId);
        });

        btnLogout = document.getElementById("btn_logout");
        btnLogout.addEventListener("click", function(e) {
            e.preventDefault();

            if (confirm('Change to another email?')) {
                clearData(refreshViews)
            }
        });
        /*
        btnAdv = document.querySelector(".btn-advanced-settings");
        btnAdv.addEventListener("click", function (e) {
            e.preventDefault();

            formInfo.classList.toggle("hide-advanced");
        });
        */

        $('#user_email').click(function () { 
           hide_notification();
           $('#user_email_help').removeClass('hidden').addClass('show');
           $('#user_device_id_help').removeClass('show').addClass('hidden');
        });

        $('#user_password').click(function () { 
           hide_notification();
           $('#user_email_help').removeClass('show').addClass('hidden');
           $('#user_device_id_help').removeClass('show').addClass('hidden');
        });

        $('#user_device_id').click(function () {
           hide_notification();
           $('#user_email_help').removeClass('show').addClass('hidden');
           $('#user_device_id_help').removeClass('hidden').addClass('show');
        });

        function hide_notification(){
           $('#error_notification').removeClass('show').addClass('hidden');
        }

        var _gaq = _gaq || [];
        _gaq.push(["_setAccount", "UA-33205486-2"]);
        _gaq.push(['_trackPageview']);

        (function() {
          var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
          ga.src = 'https://ssl.google-analytics.com/ga.js';
          var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
        })();

        /* test if still logged in */
        if (localStorage.getItem("authToken") !== null) {
            chrome.extension.getBackgroundPage().hasValidSession(function(isValid) {
                if (!isValid) {
                    refreshViews();
                }
            });
        }
    }

    var init = function() {
        initForm();
        refreshViews();
    }

    this.init = init;
}

Options.init();