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

* 
system.buildprop

* 
dalvik.vm.heapstartsize
dalvik.vm.heapgrowthlimit: maximum if android:largeHeap is not true in manifest
dalvik.vm.heapsize: 最大size

heap每次分配的大小跟当时环境有关

* svc power stayon usb // ensure screen on when charging

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

* security setting
am start -n com.android.settings/.SecuritySettings

* calculator
am start -n com.android.calculator2/.Calculator
</am>

<pm>


</pm>

<input>
input keyevent 26 // power
input tap // emulate tap
input keyevent 82 // unlock

</input>

