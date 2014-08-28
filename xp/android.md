<todo>
set up http server on android
am start content shell

* change sleep time
</todo>

<useful>
* svc power stayon usb // ensure screen on when charging
* LD_LIBRARY_PATH=/workspace/tool/adt/sdk/tools/lib /workspace/tool/adt/sdk/tools/emulator64-x86 -avd x86 -no-audio

</useful>


<general>
* adb shell su -- <cmd>
* can not connect
try unplug usb dongle on both sides
adb kill-server && sudo adb start-server
sudo service dnsmasq restart
check route
* service list

*
setprop dalvik.vm.profiler 1

setprop persist.sys.language de
setprop persist.sys.country de

*
system.buildprop

*
dalvik.vm.heapstartsize
dalvik.vm.heapgrowthlimit: maximum if android:largeHeap is not true in manifest
dalvik.vm.heapsize: 最大size

heap每次分配的大小跟当时环境有关

* build/envsetup.sh
Set lunch combo: Some combos are added here, while the others added via vendorsetup.sh. For example: device/intel/kvm_initrd_64bit/vendorsetup.sh
variant: user, userdebug, eng, etc.
gettop: root directory, e.g., /workspace/project/android-ia
lunch:
tapas: App name
croot: change the directory to the top of the tree.
m:       Makes from the top of the tree.
mm:      Builds all of the modules in the current directory, but not their dependencies.
mmm:     Builds all of the modules in the supplied directories, but not their dependencies. Can only build with directory that has Android.mk
mma:     Builds all of the modules in the current directory, and their dependencies.
mmma:    Builds all of the modules in the supplied directories, and their dependencies.



</general>


<cts>
http://static.googleusercontent.com/media/source.android.com/en/us/compatibility/android-cts-manual.pdf

switch to english
security->screen lock->None
developer options->usb debugging
developer options->stay awake
developer options->allow mock location


Compatibility Test Suite
https://source.android.com/compatibility/cts-development.html
https://static.googleusercontent.com/media/source.android.com/en/us/compatibility/android-cts-manual.pdf
</cts>

<makefile>
* Android makefile spec
http://www.kandroid.org/ndk/docs/ANDROID-MK.html

$(info Value of my_module_multilib is '$(my_module_multilib)')

* general makefiles: build/
  baytrail specific makefiles: device/intel/baytrail

</makefile>

<perf>
* Get system info
while true ;do sleep 1; adb shell cat /proc/meminfo | grep MemAvail; done
while true ;do sleep 1; adb shell cat /proc/meminfo | grep MemFree; done

*
dumpsys | grep "DUMP OF SERVICE"
dumpsys battery
dumpsys cpuinfo
dumpsys power |grep mScreenOn=true

</perf>

<debug>
<dropbox>
http://xiaocong.github.io/blog/2012/11/21/to-introduce-android-dropboxmanager-service/
dropboxmanager
/data/system/dropbox
crash, anr, wtf, strictmode, lowmem, watchdog, netstats_error, BATTERY_DISCHARGE_INFO, SYSTEM_BOOT, SYSTEM_RESTART
SYSTEM_LAST_KMSG, APANIC_CONSOLE, APANIC_THREADS, SYSTEM_RECOVERY_LOG, SYSTEM_TOMBSTONE
</dropbox>


java:
import android.util.Log;
Log.e("BrowserPreferencesPage", fragmentName);


try {
    Thread.sleep(10000);
} catch (InterruptedException e) {
    e.printStackTrace();
}


Chromium:
TODO

Skia:
TODO

</debug>


<am>
start an activity, service, broadcast intent, instrumentation, profile, monitor

start with parameter for chrome? TODO


[-e|--es <EXTRA_KEY> <EXTRA_STRING_VALUE> ...]
[--esn <EXTRA_KEY> ...]
[--ez <EXTRA_KEY> <EXTRA_BOOLEAN_VALUE> ...]
[--ei <EXTRA_KEY> <EXTRA_INT_VALUE> ...]
[--el <EXTRA_KEY> <EXTRA_LONG_VALUE> ...]
[--eu <EXTRA_KEY> <EXTRA_URI_VALUE> ...]
[--eia <EXTRA_KEY> <EXTRA_INT_VALUE>[,<EXTRA_INT_VALUE...]]
[--ela <EXTRA_KEY> <EXTRA_LONG_VALUE>[,<EXTRA_LONG_VALUE...]]

* instrument test
am instrument -w com.android.browser.tests/android.test.InstrumentationTestRunner

* stock browser
am start -a android.intent.action.VIEW -n com.android.browser/.BrowserActivity -d http://www.baidu.com
am start -a android.intent.action.VIEW -n com.android.browser/.BrowserActivity -d file:///data/local/tmp/index.html

* chrome stable
adb shell am start -n com.android.chrome/com.android.chrome.Main -d "chrome://version"

* chrome beta
adb shell am start -n com.chrome.beta/com.chrome.beta.Main -d "chrome://version"

* content shell
adb shell am start -n org.chromium.content_shell/.ContentShellApplication -d "about:version"

* security setting
am start -n com.android.settings/.SecuritySettings

* calculator
am start -n com.android.calculator2/.Calculator

* developer options
adb shell am start -n com.android.settings/.DevelopmentSettings
</am>

<pm>


</pm>

<input>
input keyevent 26 // power
input tap // emulate tap
input keyevent 82 // unlock

</input>

<tethering>
desktop shares the connection of android device

192.168.42.51

* wireless & networks -> More... -> Tethering & portable hotspot -> usb tethering
* bridge the interface (usb0 is the new network intreface, eth0 is the main interface connected to internet)
sudo ifconfig eth0 0.0.0.0
sudo ifconfig usb0 0.0.0.0
sudo brctl addbr br0
sudo brctl addif br0 eth0
sudo brctl addif br0 usb0
sudo ifconfig br0 up
sudo dhclient br0

*
./adb shell netcfg usb0 dhcp

<tethering>

<reverse_tethering>
android device shares the connection of desktop

Host:
# configurate interface
# ifconfig eth1 inet 192.168.42.2
# enable ip forwarding
# echo 1 > /proc/sys/net/ipv4/ip_forward
# configurate NAT

ubuntu-ygu5-01:
INTERNAL=eth0
EXTERNAL=eth1

ubuntu-ygu5-02:
INTERNAL=eth3
EXTERNAL=eth0

sudo iptables -t nat -A POSTROUTING -o $EXTERNAL -j MASQUERADE
sudo iptables -A FORWARD -i $EXTERNAL -o $INTERNAL -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i $INTERNAL -o $EXTERNAL -j ACCEPT

Target:
# Add routing & DNS
route add default gw 192.168.42.2 dev eth0
/system/bin/dnsmasq -2 -x -i lo -S 10.248.2.5 --pid-file

</reverse_tethering>