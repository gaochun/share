<commit>
20131119 r236024 Android: Reenable canvas anti-aliasing

</commit>   

Run '/usr/bin/python src/build/util/lastchange.py -o src/build/util/LASTCHANGE' in '/workspace/project/webcatch/project/chromium-linux'
Run '/usr/bin/python src/build/util/lastchange.py -s src/third_party/WebKit -o src/build/util/LASTCHANGE.blink' in '/workspace/project/webcatch/project/chromium-linux'

#<font color="red">[general]</font>#

void WebLayerTreeViewImpl::composite() // webkit/compositor_bindings/WebLayerTreeViewImpl.cpp 决定是否用threaded compositor

## cycle of life ##
有2个buffer，A和B。准备A的数据，swap buffer到A。swap到A后并不是等完成再准备B。而是先执行B的JS code，然后等待swap buffer到A完成，再render，composite，完成B的数据准备，再swap buffer到B。
显示器总是以一定频率刷新，不停的显示current buffer。

## start of processes ##
    main (chrome_exe_main_gtk.cc:18)     // There are other entries, such as main in chrome/app/chrome_exe_main_aura.cc
        ChromeMain (chrome/app/chrome_main.cc:32)
            content::ContentMain (content/app/content_main.cc:35)
                ContentMainRunnerImpl::Initialize
                    RunNamedProcessTypeMain(process_type, main_params, delegate_);
                    BrowserMain // entry of browser process, content/browser/browser_main.cc
                    GpuMain // entry of GPU process, content/gpu/gpu_main.cc
                        RunZygote(main_function_params, delegate); // content/app/content_main_runner.cc
                            return kMainFunctions[i].function(main_params);
                                RendererMain // entry of render, content/renderer/renderer_main.cc:241, name is CrRendererMain


## renderer tree creation ##
    Node::attach (third_party/WebKit/Source/WebCore/dom/Node.cpp)
        Node::createRendererIfNeeded
            NodeRendererFactory::createRendererIfNeeded
                NodeRendererFactory::createRenderer
                    Node::createRenderer
                        HTMLCanvasElement::createRenderer  (HTMLCanvasElement is descendent of Node)
                            RenderObject::createObject

## renderlayer tree creation ##
    Node::createRendererIfNeeded
        NodeRendererFactory::createRendererIfNeeded
            NodeRendererFactory::createRenderer
                RenderObject::setAnimatableStyle
                    RenderObject::setStyle
                        RenderReplaced::styleDidChange
                            RenderBox::styleDidChange
                                RenderBoxModelObject::styleDidChange
                                    RenderReplaced::requiresLayer
                                        RenderBox::requiresLayer (third_party/WebKit/Source/WebCore/rendering/RenderBox.h) //
                                    RenderHTMLCanvas::requiresLayer (third_party/WebKit/Source/WebCore/rendering/RenderHTMLCanvas.cpp // To decide if a new layer is needed. TODO: it seems this function would be accessed twice, why?

 


#<font color="red">[/general]</font>#

#<font color="red">[switch_flag]</font>#

## all the switches ##
content/public/common/content_switches.cc|h  
switches::kEnableAccelerated2dCanvas

## settings ##
WebKit/Source/WebCore/page/Settings.cpp  
m_acceleratedCanvas2dEnabled

## about flags ##
chrome/browser/ui/webui/flags_ui.cc  
chrome/app/generated_resources.grd  
chrome/browser/about_flags.cc  
ui/base/ui_base_switches.(cc|h) 

    ContentMain (content/app/content_main.cc)
        main_ContentMainRunnerImpl.initialize (/content/app/content_main_runner.cc)
            CommandLine::Init(argc, argv); // put switch into argv
                CommandLine::CommandLine
                InitFromArgv // posix
                    CommandLineToArgvW

#<font color="red">[/switch_flag]</font>#

#<font color="red">[gc]</font>#
gc is triggered by LowMemoryNotification or IdleNotification

*LowMemoryNotification*

    TaskManagerView::ButtonPressed // purge_memory_button_ in task manager is pressed
        MemoryPurger::PurgeAll()
            MemoryPurger::PurgeRenderers         
                MemoryPurger::PurgeRendererForHost
                    ChromeViewMsg_PurgeMemory  // IPC_MESSAGE_HANDLER(ChromeViewMsg_PurgeMemory, OnPurgeMemory)
                        ChromeRenderProcessObserver::OnPurgeMemory         
                            v8::V8::LowMemoryNotification
                                CollectAllAvailableGarbage
									Heap::CollectGarbage 

*IdleNotification*

    RenderThreadImpl::ScheduleIdleHandler
        RenderThreadImpl::IdleHandler  // src/content/renderer/render_thread_impl.cc, will adjust next idle time(dampening effect, Zu Ni Xiao Ying)
            v8::V8::IdleNotification
                Heap::IdleNotification  //
                    Heap::CollectAllGarbage // full garbage collection
                        Heap::CollectGarbage     // v8/src/heap.cc
                            GarbageCollectionPrologue
                            PerformGarbageCollection
                            GarbageCollectionEpilogue
                   
                   
**how to expose gc to JS**

Name is after const char* const GCExtension::kSource = "native function gc();"; (v8/src/extensions/gc-extension.cc)  

if (FLAG_expose_gc) in v8/src/bootstrapper.cc

    V8DOMWindowShell::initContextIfNeeded  // third_party/WebKit/Source/WebCore/bindings/v8/V8DOMWindowShell.cpp, V8 initializes context
        createNewContext(m_global, 0, 0);    
            V8DOMWindowShell::createNewContext
                v8::Context::New(&extensionConfiguration, globalTemplate, global);
                    Bootstrapper::CreateEnvironment
                        Bootstrapper::InstallExtensions
                            Genesis::InstallExtensions
                                InstallExtension("v8/gc", &extension_states)
         
gc() in javascript will map to CollectAllGarbage()

    checkMemoryUsage  // third_party/WebKit/Source/WebCore/bindings/v8/V8GCController.cpp
        isolate->heap()->CollectAllAvailableGarbage("low memory notification");

    third_party/WebKit/Source/Platform/chromium/public/Platform.h
        if ((memoryUsageMB > lowMemoryUsageMB && memoryUsageMB > 2 * workingSetEstimateMB) || (memoryUsageMB > highMemoryUsageMB && memoryUsageMB > workingSetEstimateMB + highUsageDeltaMB))

        // If memory usage is below this threshold, do not bother forcing GC.
        virtual size_t lowMemoryUsageMB() { return 256; }

        // If memory usage is above this threshold, force GC more aggressively.
        virtual size_t highMemoryUsageMB() { return 1024; }

        // Delta of memory usage growth (vs. last actualMemoryUsageMB()) to force GC when memory usage is high.
        virtual size_t highUsageDeltaMB() { return 128; }    
    
#<font color="red">[/gc]</font>#


#<font color="red">[canvas]</font>#
## Create canvas based on SkGpuDevice ##
    CanvasRenderingContext2D::fillRect 
        CanvasRenderingContext2D::drawingContext
            ImageBuffer::ImageBuffer
                if (renderingMode == Accelerated) SkCanvas* createAcceleratedCanvas (WebKit/Source/WebCore/platform/graphics/skia/ImageBufferSkia.cpp)
                    new SkGpuDevice(GrContext, GrTexture)
                    new SkCanvas(device.get());

## draw bitmap ##
    SkCanvas::commonDrawBitmap
        SkGpuDevice::drawBitmap     // hardware rendering
            SkGpuDevice::internalDrawBitmap
                GrContext::drawRectToRect
                    GrDrawTarget::drawRect
                        GrDrawTarget::drawNonIndexed
                            GrGpu::onDrawNonIndexed
                                GrGpuGL::onGpuDrawNonIndexed

        SkCanvas::drawBitmap     // software rendering
            SkDevice::drawBitmap
                SkDraw::drawBitmap
                    SkScan::FillIRect
                        Sprite_D32_S32::blitRect

## fill rect ##
    v8::Handle<v8::Value> fillRectCallback (src/out/Debug/obj/gen/webcore/bindings/V8CanvasRenderingContext2D.cpp)     // v8 binding
        CanvasRenderingContext2D::fillRect  // hw fillRect
            GraphicsContext::fillRect
                SkCanvas::drawRect
                    SkGpuDevice::drawRect
                        GrContext::drawRect
                            GrDrawTarget::drawNonIndexed
                                GrGpu::onDrawNonIndexed
                                    GrGpuGL::onGpuDrawNonIndexed
                                        GL_CALL(DrawArrays(gPrimitiveType2GLMode[type], 0, vertexCount));
            CanvasRenderingContext2D::didDraw  // immediate draw
                RenderBoxModelObject::contentChanged  

## composite ##
    RenderWidget::InvalidationCallback
        RenderWidget::DoDeferredUpdateAndSendInputAck
            RenderWidget::DoDeferredUpdate
                WebViewImpl::composite
                    if USE(ACCELERATED_COMPOSITING) WebLayerTreeView::composite
                        CCLayerTreeHost::composite
                            CCSingleThreadProxy::compositeImmediately (WebKit/Source/WebCore/platform/graphics/chromium/cc/CCSingleThreadProxy.cpp)
                                    CCSingleThreadProxy::commitAndComposite
                                        CCLayerTreeHost::updateLayers
                                            CCLayerTreeHost::updateLayers
                                                CCLayerTreeHost::paintLayerContents
                                                    CCLayerTreeHost::update
                                                        Canvas2DLayerChromium::update
                                        CCSingleThreadProxy::doComposite
                                            CCLayerTreeHostImpl::drawLayers
                                    CCLayerTreeHostImpl::swapBuffers     // send command to GPU swap buffer to finish the display
                                        LayerRendererChromium::swapBuffers
                                            GraphicsContext3D::prepareTexture
                                                WebGraphicsContext3DCommandBufferImpl::prepareTexture
                                                    GLES2Implementation::SwapBuffers

## paint related ##
    FrameView::paintContents
        RenderLayer::paint
            RenderLayer::paintLayer
                RenderLayer::paintLayerContentsAndReflection
                    RenderLayer::paintLayerContents // exit: jump to RenderReplaced::paint
                        RenderLayer::paintList  // loop to RenderLayer::paintLayer
                            RenderReplaced::paint
                                RenderHTMLCanvas::paintReplaced
                                    HTMLCanvasElement::paint


DEBUG_GL_CALLS 可以设置成1, 用于调试。



    CanvasRenderingContext2D::fillRect  // third_party/WebKit/Source/WebCore/html/canvas/CanvasRenderingContext2D.idl|h|cpp
        GraphicsContext::fillRect  // third_party/WebKit/Source/WebCore/platform/graphics/skia/GraphicsContextSkia.cpp
            GraphicsContext::drawRect
                PlatformContextSkia::drawRect
                    SkCanvas::DrawRect  // third_party/skia/src/core/SkCanvas.cpp
                        SkDevice::drawRect  // third_party/skia/src/core/SkDevice.cpp, sw handling
                            SkDraw::drawRect // third_party/skia/src/core/SkDraw.cpp
                        SkGpuDevice::drawRect // third_party/skia/src/gpu/SkGpuDevice.cpp, hw acceleration
                            GrContext::drawRect
                                GrDrawTarget::drawNonIndexed
                                    GrGpu::onDrawNonIndexed
                                        GrGpuGL::onGpuDrawNonIndexed
                                            GL_CALL(DrawArrays(gPrimitiveType2GLMode[type], 0, vertexCount));  // third_party/skia/src/gpu/gl/GrGpuGL.cpp (这里适合bp)
                                                GLES2DrawArrays // gpu/command_buffer/client/gles2_c_lib_autogen.h
                                                    GLES2Implementation::DrawArrays // gpu/command_buffer/client_gles2_implementation.cc
                                                        DrawArrays // gpu/command_buffer_client/gles2_cmd_helper_autogen.h      


* render process stack
GrGpuGL::onGpuDrawNonIndexed() at GrGpuGL.cpp:1,730 0xb0c5d1b1	
GrGpu::onDrawNonIndexed() at GrGpu.cpp:439 0xb0c1f1c1	
GrDrawTarget::drawNonIndexed() at GrDrawTarget.cpp:793 0xb0c1b17d	
GrContext::drawRect() at GrContext.cpp:878 0xb0c10d47	
GrContext::drawPaint() at GrContext.cpp:672 0xb0c1029e	
SkGpuDevice::drawPaint() at SkGpuDevice.cpp:643 0xb0c359c1	
SkCanvas::internalDrawPaint() at SkCanvas.cpp:1,444 0xb0b5c3f7	
SkCanvas::drawPaint() at SkCanvas.cpp:1,437 0xb0b5c330	
SkPicturePlayback::draw() at SkPicturePlayback.cpp:625 0xb0ba80bd	
SkPicture::draw() at SkPicture.cpp:195 0xb0ba5024	
SkDeferredCanvas::DeferredDevice::flushPending() at SkDeferredCanvas.cpp:519 0xb0c920c7	
SkDeferredCanvas::DeferredDevice::flush() at SkDeferredCanvas.cpp:526 0xb0c92145	
SkCanvas::flush() at SkCanvas.cpp:526 0xb0b5998c	
WebCore::Canvas2DLayerBridge::prepareTexture() at Canvas2DLayerBridge.cpp:134 0xabfe1157	
WebKit::WebExternalTextureLayerImpl::prepareTexture() at WebExternalTextureLayer.cpp:66 0xaaf015bb	
WebCore::TextureLayerChromium::update() at TextureLayerChromium.cpp:135 0xac0d3c9d	
WebCore::CCLayerTreeHost::paintLayerContents() at CCLayerTreeHost.cpp:611 0xac0fb2e7	
WebCore::CCLayerTreeHost::updateLayers() at CCLayerTreeHost.cpp:493 0xac0fab1e	
WebCore::CCLayerTreeHost::updateLayers() at CCLayerTreeHost.cpp:459 0xac0fa752	
WebCore::CCSingleThreadProxy::commitAndComposite() at CCSingleThreadProxy.cpp:315 0xac1296fe	
WebCore::CCSingleThreadProxy::compositeImmediately() at CCSingleThreadProxy.cpp:288 0xac1295a3	
WebCore::CCLayerTreeHost::composite() at CCLayerTreeHost.cpp:422 0xac0fa5b2	
WebKit::WebLayerTreeView::composite() at WebLayerTreeView.cpp:160 0xaaf30d3d	
WebKit::WebViewImpl::composite() at WebViewImpl.cpp:1,660 0xaaf5ccea	
RenderWidget::DoDeferredUpdate() at render_widget.cc:987 0xb1f369fd	
RenderWidget::DoDeferredUpdateAndSendInputAck() at render_widget.cc:808 0xb1f3542a	
RenderWidget::InvalidationCallback() at render_widget.cc:804 0xb1f353fa	
base::internal::RunnableAdapter<void () at bind_internal.h:134 0xb1f3cb28	
base::internal::InvokeHelper<false, void, base::internal::RunnableAdapter<void () at bind_internal.h:870 0xb1f3c74b	
base::internal::Invoker<1, base::internal::BindState<base::internal::RunnableAdapter<void () at bind_internal.h:1,172 0xb1f3c350	
base::Callback<void () at callback.h:388 0xb4ecbcc8	
MessageLoop::RunTask() at message_loop.cc:456 0xb4f05c0d	
MessageLoop::DeferOrRunPendingTask() at message_loop.cc:468 0xb4f05d06	
MessageLoop::DoWork() at message_loop.cc:644 0xb4f064a9	
base::MessagePumpDefault::Run() at message_pump_default.cc:28 0xb4f0e3c6	
MessageLoop::RunInternal() at message_loop.cc:415 0xb4f05908	
MessageLoop::RunHandler() at message_loop.cc:388 0xb4f057e1	
base::RunLoop::Run() at run_loop.cc:45 0xb4f36258	
MessageLoop::Run() at message_loop.cc:299 0xb4f05122	
RendererMain() at renderer_main.cc:271 0xb1f492d6	
content::RunZygote() at content_main_runner.cc:330 0xb19c03bd	
content::RunNamedProcessTypeMain() at content_main_runner.cc:383 0xb19c057b	
content::ContentMainRunnerImpl::Run() at content_main_runner.cc:630 0xb19c1218	
content::ContentMain() at content_main.cc:35 0xb19bfc04	
ChromeMain() at chrome_main.cc:32 0xb53bdfef	
main() at chrome_exe_main_gtk.cc:18 0xb53bdfa3	



* GPU process stack  
glDrawArrays(mode, first, count); // 最后调用gl的函数， gpu/command_buffer/service/gles2_cmd_decoder.cc
gpu::gles2::GLES2DecoderImpl::DoDrawArrays() at gles2_cmd_decoder.cc:5,516 0xa97b4220	
gpu::gles2::GLES2DecoderImpl::HandleDrawArrays() at gles2_cmd_decoder.cc:5,593 0xa97b467b	
gpu::gles2::GLES2DecoderImpl::DoCommand() at gles2_cmd_decoder.cc:3,213 0xa97aa702	
gpu::CommandParser::ProcessCommand() at cmd_parser.cc:72 0xa9793643	
gpu::GpuScheduler::PutChanged() at gpu_scheduler.cc:81 0xa97d1ec7	
GpuCommandBufferStub::PutChanged() at gpu_command_buffer_stub.cc:640 0xb1e49234	
base::internal::RunnableAdapter<void () at bind_internal.h:134 0xb1e50bfe	
base::internal::InvokeHelper<false, void, base::internal::RunnableAdapter<void () at bind_internal.h:870 0xb1e500dc	
base::internal::Invoker<1, base::internal::BindState<base::internal::RunnableAdapter<void () at bind_internal.h:1,172 0xb1e4efa5	
base::Callback<void () at callback.h:388 0xa97944da	
gpu::CommandBufferService::Flush() at command_buffer_service.cc:88 0xa9793cf8	
GpuCommandBufferStub::OnAsyncFlush() at gpu_command_buffer_stub.cc:525 0xb1e48a99	
DispatchToMethod<GpuCommandBufferStub, void () at tuple.h:553 0xb1e4d0e0	
GpuCommandBufferMsg_AsyncFlush::Dispatch<GpuCommandBufferStub, GpuCommandBufferStub, void () at gpu_messages.h:402 0xb1e4afb1	
GpuCommandBufferStub::OnMessageReceived() at gpu_command_buffer_stub.cc:153 0xb1e45e0a	
MessageRouter::RouteMessage() at message_router.cc:47 0xb1e89936	
GpuChannel::HandleMessage() at gpu_channel.cc:434 0xb1e3abf9	
base::internal::RunnableAdapter<void () at bind_internal.h:134 0xb1e40068	
base::internal::InvokeHelper<true, void, base::internal::RunnableAdapter<void () at bind_internal.h:882 0xb1e3f75d	
base::internal::Invoker<1, base::internal::BindState<base::internal::RunnableAdapter<void () at bind_internal.h:1,172 0xb1e3e945	
base::Callback<void () at callback.h:388 0xb4f3bcc8	
MessageLoop::RunTask() at message_loop.cc:456 0xb4f75c0d	
MessageLoop::DeferOrRunPendingTask() at message_loop.cc:468 0xb4f75d06	
MessageLoop::DoWork() at message_loop.cc:644 0xb4f764a9	
base::MessagePumpDefault::Run() at message_pump_default.cc:28 0xb4f7e3c6	
MessageLoop::RunInternal() at message_loop.cc:415 0xb4f75908	
MessageLoop::RunHandler() at message_loop.cc:388 0xb4f757e1	
base::RunLoop::Run() at run_loop.cc:45 0xb4fa6258	
MessageLoop::Run() at message_loop.cc:299 0xb4f75122	
GpuMain() at gpu_main.cc:229 0xb1ec5e79	
content::RunNamedProcessTypeMain() at content_main_runner.cc:375 0xb1a3053c	
content::ContentMainRunnerImpl::Run() at content_main_runner.cc:630 0xb1a31218	
content::ContentMain() at content_main.cc:35 0xb1a2fc04	
ChromeMain() at chrome_main.cc:32 0xb542dfef	
main() at chrome_exe_main_gtk.cc:18 0xb542dfa3	

#<font color="red">[/canvas]</font>#

#<font color="red">[deferred_canvas]</font>#
    CanvasRenderingContext2D::fillRect  // third_party/WebKit/Source/WebCore/html/canvas/CanvasRenderingContext2D.cpp
        CanvasRenderingContext2D::drawingContext
            HTMLCanvasElement::drawingContext
                HTMLCanvasElement::buffer
                    HTMLCanvasElement::createImageBuffer
                        DeferralMode deferralMode = shouldDefer() ? Deferred : NonDeferred;
                        ImageBuffer::create(size(), m_deviceScaleFactor, ColorSpaceDeviceRGB, renderingMode, deferralMode);

    HTMLCanvasElement::createImageBuffer // third_party/WebKit/Source/WebCore/html/HTMLCanvasElement.cpp
        m_imageBuffer = ImageBuffer::create(size(), m_deviceScaleFactor, ColorSpaceDeviceRGB, renderingMode, deferralMode);
            ImageBuffer::ImageBuffer
                createAcceleratedCanvas(size, &m_data, deferralMode) // third_party/WebKit/Source/WebCore/platform/graphics/skia/ImageBufferSkia.cpp
                    Canvas2DLayerBridge::create  // third_party/WebKit/Source/WebCore/platform/graphics/chromium/Canvas2DLayerBridge.cpp
                    anvas2DLayerBridge::skCanvas
                        new SkDeferredCanvas
 
#<font color="red">[/deferred_canvas]</font>#

#<font color="red">[FPS]</font>#
* FPS有几个地方体现
@ 通过about:flags打开的FPS。只有在硬件打开的时候才能用。
@ task manager里面显示的。
@ timeline里面显示的。如果时间超过1秒，丢掉.
这3个都不同。
我们应该算的是average FPS，是把合理的FPS(每一帧都可以算出FPS)求一个平均。
TODO：我觉得软件和硬件FPS可以统一。task manager和fps count可以统一。
FPS其实是记录开始时间，由下一帧的开始时间决定上一帧的结束时间.

chrome/test/perf/rendering/throughput_tests.cc 计算FPS，是拿总帧数/总时间

## Task manager ##
    TaskManagerGtk::Show // chrome/browser/ui/gtk/task_manager_gtk.cc, 响应了快捷键，task manager显示出来
        TaskManagerModel::StartUpdating  // chrome/browser/task_manager/task_manager.cc
            TaskManagerModel::Refresh
                TaskManagerRendererResource::Refresh  // (*iter)->Refresh();
                    render_view_host_->Send(new ChromeViewMsg_GetFPS(render_view_host_->GetRoutingID())); // renderer process will send back fps
                        ChromeRenderViewObserver::OnGetFPS // IPC_MESSAGE_HANDLER(ChromeViewMsg_GetFPS, OnGetFPS)，chrome/renderer/chrome_render_view_observer.cc
                            float fps = (render_view()->GetFilteredTimePerFrame() > 0.0f)?1.0f / render_view()->GetFilteredTimePerFrame() : 0.0f; 
                                GetFilteredTimePerFrame
                                    filtered_time_per_frame
                                        return filtered_time_per_frame_ // 这个值在DoDeferredUpdate时生成，不是那么平均。
                            Send(new ChromeViewHostMsg_FPS(routing_id(), fps)); 
                                ChromeRenderMessageFilter::OnFPS // IPC_MESSAGE_HANDLER(ChromeViewHostMsg_FPS, OnFPS), chrome/browser/render_host/chrome_render_message_filter.cc
                                    TaskManagerModel::NotifyFPS
                                        TaskManagerRendererResource::NotifyFPS  


## RequestionAnimationFrame ##
    define MinimumAnimationInterval 0.015 // 
    third_party/.../WebCore/dom/ScriptedAnimationController.cpp
        ScriptedAnimationController::scheduleAnimation() 
            double scheduleDelay = max<double>(MinimumAnimationInterval - (currentTime() - m_lastAnimationFrameTime), 0);
            m_animationTimer.startOneShot(scheduleDelay);

## CSS ##
    static const double cAnimationTimerDelay = 0.025; // third_party/.../WebCore/page/animation/AnimationController.cpp. 所以CSS最高是40fps


    CCLayerTreeHostImpl::drawLayers // cc/CCLayerTreeHostImpl.cpp
        CCHeadsUpDisplayLayerImpl::updateHudTexture
            CCHeadsUpDisplayLayerImpl::drawHudContents

## Overall ##
    RenderWidget::DoDeferredUpdate // content/renderer/render_widget.cc
        filtered_time_per_frame_ = 0.9f * filtered_time_per_frame_ + 0.1f * frame_time_elapsed;  // 最后task manager用这个值
        UNSHIPPED_TRACE_EVENT_INSTANT0("test_fps", "TestFrameTickSW"); // 软件加速, !is_accelerated_compositing_active_
        webwidget_->composite(false); // GPU accelerated
            WebViewImpl::composite // WebKit/chromium/src/WebViewImpl.cpp
                WebLayerTreeViewImpl::composite
                    CCLayerTreeHost::composite
                        CCSingleThreadProxy::compositeImmediately // cc/CCSingleThreadProxy.cpp, called from render_widget scheduling, which is legacy
                            CCSingleThreadProxy::commitAndComposite
                                CCLayerTreeHost::updateLayers
                                    CCLayerTreeHost::paintLayerContents
                                        ContentLayerChromium::update
                                            TiledLayerChromium::update
                                                TiledLayerChromium::updateTiles
                                                    TiledLayerChromium::updateTileTextures
                                                        BitmapCanvasLayerTextureUpdater::prepareToUpdate
                                                            CanvasLayerTextureUpdater::paintContents
                                                                ContentLayerPainter::paint
                                                                    WebContentLayerImpl::paintContents
                                                                        OpaqueRectTrackingContentLayerDelegate::paintContents
                                                                            GraphicsLayerChromium::paint
                                                                                GraphicsLayer::paintGraphicsLayerContents
                                                                                    RenderLayerBacking::paintContents
                                                                                        InspectorInstrumentation::willPaint
                                                                                            InspectorInstrumentation::willPaintImpl
                                                                                                InspectorTimelineAgent::willPaint
                                                                                                    InspectorTimelineAgent::pushCurrentRecord
                                                                                                        InspectorTimelineAgent::commitFrameRecord  // WebCore/inspector/InspectorTimelineAgent.cpp
                                CCSingleThreadProxy::doComposite
                                    CCLayerTreeHostImpl::drawLayers
                                        m_fpsCounter->markBeginningOfFrame(currentTime()); // cc/CCFrameRateCounter.cpp
                                        CCHeadsUpDisplayLayerImpl::updateHudTexture 
                                            CCHeadsUpDisplayLayerImpl::drawHudContents
                                                CCHeadsUpDisplayLayerImpl::drawFPSCounter // 真正画fps counter。用了markBeginningOfFrame()里面记录的值，是真正的平均值，只是硬件加速的值。                                    
                            CCLayerTreeHostImpl::swapBuffers
                                m_fpsCounter->markEndOfFrame();
                                CCRendererGL::swapBuffers
                                    WebGraphicsContext3DCommandBufferImpl::prepareTexture
                                        WebGraphicsContext3DCommandBufferImpl::OnSwapBuffersComplete // content/common/gpu/client/webgraphicscontext3d_command_buffer_impl.cc.  command_buffer_->Echo(base::Bind(&WebGraphicsContext3DCommandBufferImpl::OnSwapBuffersComplete
                                            RenderViewImpl::OnViewContextSwapBuffersComplete  // MessageLoop::current()->PostTask(FROM_HERE, base::Bind(&WGC3DSwapClient::OnViewContextSwapBuffersComplete, swap_client_));
                                                RenderWidget::OnSwapBuffersComplete
                                                    RenderWidget::DoDeferredUpdateAndSendInputAck 
                                                        RenderWidget::DoDeferredUpdate				

                            CCSingleThreadProxy::didSwapFrame  // if (m_nextFrameIsNewlyCommittedFrame)
                                didCommitAndDrawFrame
                                    WebLayerTreeViewImpl::didCommitAndDrawFrame
                                        WebViewImpl::didCommitAndDrawFrame
                                            RenderWidget::didCommitAndDrawCompositorFrame
                                                UNSHIPPED_TRACE_EVENT_INSTANT0("test_fps", "TestFrameTickGPU"); // 在这里做最合理

#<font color="red">[/FPS]</font>#

#<font color="red">[gpu]</font>#

#<font color="red">[/gpu]</font>#

#<font color="red">[Template]</font>#
#<font color="red">[]</font>#
#<font color="red">[/Template]</font>#