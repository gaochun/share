LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

LOCAL_CFLAGS += -fPIE
LOCAL_LDFLAGS += -fPIE -pie
LOCAL_MODULE    := allocate_memory
LOCAL_SRC_FILES := allocate_memory.c

include $(BUILD_EXECUTABLE)

