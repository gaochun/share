<todo>
set up http server on android
am start content shell

* change sleep time
</todo>

<useful>
* svc power stayon usb // ensure screen on when charging
* LD_LIBRARY_PATH=/workspace/tool/adt/sdk/tools/lib /workspace/tool/adt/sdk/tools/emulator64-x86 -avd x86 -no-audio

* screen
power + volumn down
adb shell screenrecord /sdcard/fail.mp4

* delete gms chrome
rm -rf /system/app/Chrome

* install stock browser
cd /system/app/BrowserProviderPorxy && mv BrowserProviderProxy.apk BrowserProviderProxy.apk.bk, restart
adb install Browser.apk

* adb out of date
There is a background adb process in host machine. restart host machine to resolve the issue.
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

*
tools/cts-tradefed
run cts -c android.webgl.cts.WebGLTest -m test_conformance_textures_tex_image_and_sub_image_2d_with_canvas_html

adb pull /data/data/android.webgl.cts/cache/tests/conformance/textures/tex-image-and-sub-image-2d-with-canvas.html && adb pull /data/data/android.webgl.cts/cache/tests/resources/js-test-style.css && adb pull /data/data/android.webgl.cts/cache/tests/resources/js-test-pre.js && adb pull /data/data/android.webgl.cts/cache/tests/conformance/resources/webgl-test-utils.js && adb pull /data/data/android.webgl.cts/cache/tests/conformance/resources/tex-image-and-sub-image-2d-with-canvas.js

adb shell am start -n com.android.chrome/com.android.chrome.Main -d "http://wp-02.sh.intel.com/WebGL/conformance-suites/1.0.2/conformance/textures/tex-image-and-sub-image-2d-with-canvas.html"

adb shell am start -n com.android.chrome/com.android.chrome.Main -d "http://wp-02.sh.intel.com/gytemp/tex-image-and-sub-image-2d-with-canvas/conformance/textures/tex-image-and-sub-image-2d-with-canvas.html"

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

* adb logcat -v threadtime -b main -b system -b events
* tcp dump
adb shell setprop dev.log.cws.wifi.dump ON (to make sure /system/xbin/tcpdump is running)
* ro.sf.lcd_density


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


<gdb>
http://www.chromium.org/developers/how-tos/debugging-on-android

*
Get WebKit code to output to the adb log
In your build environment:
adb root
adb shell stop
adb shell setprop log.redirect-stdio true
adb shell start
In the source itself, use fprintf(stderr, "message"); whenever you need to output a message.

* unit test
build/android/test_runner.py gtest -s <name_of_test_suite> -a --wait-for-debugger -t 6000
build/android/adb_gdb org.chromium.native_test   --gdbserver=third_party/android_tools/ndk_experimental/prebuilt/android-x86_64/gdbserver/gdbserver --gdb=third_party/android_tools/ndk_experimental/toolchains/x86_64-4.8/prebuilt/linux-x86_64/bin/x86_64-linux-android-gdb --target-arch=x86_64

* content_shell
build/android/adb_content_shell_command_line --wait-for-debugger
build/android/adb_gdb_content_shell --start --gdbserver=third_party/android_tools/ndk_experimental/prebuilt/android-x86_64/gdbserver/gdbserver --gdb=third_party/android_tools/ndk_experimental/toolchains/x86_64-4.8/prebuilt/linux-x86_64/bin/x86_64-linux-android-gdb --target-arch=x86_64

* aosp browser
adb connect 192.168.42.1
adb shell mount -o remount,rw /system
cd path_to_chromeforandroid_upstream
adb push third_party/android_tools/ndk_experimental/prebuilt/android-x86_64/gdbserver/gdbserver /system/bin/
adb shell sync
adb forward tcp:1234 tcp:1234
adb shell gdbserver :1234 --attach <browser pid>
cd path_to_chromium-org_in_aosp
run gdbclient in chromeforandroid_upstream: path_2_chromeforandroid_upstream/third_party/android_tools/ndk_experimental/toolchains/x86_64-4.8/prebuilt/linux-x86_64/bin/x86_64-linux-android-gdb
(gdb)target remote :1234
(gdb)set solib-absolute-prefix path_2_aosp/out/target/product/baytrail_64/symbols/
(gdb)set solib-search-path path_2_aosp/out/target/product/baytrail_64/symbols/system/lib64/
(gdb) b function
(gdb) continue

To make the webview stop for debug very early, make below changes to content/app/android/content_main.cc
1. Include the header "base/debug/debugger.h"
2. Add a line 'base::debug::WaitForDebugger(30, true);' at the begin of Start() function

* aosp browser (my xp)
adb shell ps |grep com.android.browser |awk '{print $2}' |xargs adb shell gdbserver :1234 --attach
adb forward tcp:1234 tcp:1234

/workspace/project/chromium-android/src/third_party/android_tools/ndk/toolchains/x86-4.8/prebuilt/linux-x86_64/bin/i686-linux-android-gdb
(gdb)
target remote :1234
set solib-search-path /workspace/project/aosp-gminl/out/target/product/ecs_e7/symbols/system/lib/

GrPrintf

b GrGpuGL.cpp:1426
b GrGpu.cpp:234
b GrPaint.cpp:47
b GrContext::drawRect
b GrContext.cpp:830
b GrInOrderDrawBuffer.cpp:665

        kDraw_Cmd           = 1,
        kStencilPath_Cmd    = 2,
        kSetState_Cmd       = 3,
        kSetClip_Cmd        = 4,
        kClear_Cmd          = 5,
        kCopySurface_Cmd    = 6,
        kDrawPath_Cmd       = 7,
        kDrawPaths_Cmd      = 8,

clearRect() -> transparent black (0x00000000)
16777215=FFFFFF
fColor = 0xFF000000

adb push /workspace/project/aosp-gminl/out/target/product/ecs_e7/system/lib/libwebviewchromium.so /system/lib/
adb shell stop && adb shell start

</gdb>

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

* self-build chrome
adb shell am start -n com.android.chromium/com.google.android.apps.chrome.Main -d "chrome://version"

* security setting
am start -n com.android.settings/.SecuritySettings

* calculator
am start -n com.android.calculator2/.Calculator

* developer options
adb shell am start -n com.android.settings/.DevelopmentSettings

* google music
com.google.android.music/com.android.music.activitymanagement.TopLevelActivity
start -n com.google.android.music/.MusicPicker -d content://media/external/audio/media

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

<bkm>

</bkm>