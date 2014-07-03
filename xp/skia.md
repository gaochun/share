GR_GL_RGBA      0x1908
GR_GL_RGBA8    0x8058

GR_GL_BGRA      0x80E1
GR_GL_BGRA8    0x93A1 (不对)
GR_GL_INVALID_ENUM                   0x0500

<WritePixels>
createDevice: bmp/GPU bmp->SkBitmap::kARGB_8888_Config, GPU->kSkia8888_GrPixelConfig
setupBitmap: 用6种不同配置config8888，生成bmp
canvas.writePixels: 把bmp写到canvas，用config8888做参数。config8888->GrPixelConfig->GrTextureDesc
checkWrite: 比较bmp和canvas

WritePixelsTest
    SkCanvas::writePixels  //SkCanvas::kBGRA_Unpremul_Config8888
        SkGpuDevice::writePixels
            GrRenderTarget::writePixels
                GrContext::writeRenderTargetPixels (src/gpu/GrContext.cpp)
                    GrAutoScratchTexture::GrAutoScratchTexture
                        GrAutoScratchTexture::set
                            GrContext::lockAndRefScratchTexture
                                create_scratch_texture (src/gpu/GrContext.cpp)
                                    GrGpu::createTexture
                                        GrGpuGL::onCreateTexture
                                            GrGpuGL::uploadTexData ()

GL_EXT_texture_format_BGRA8888
GL_EXT_texture_storage

src/gpu/gl/GrGLCaps.cpp fBGRAIsInternalFormat = true;

IA phone:
endian: RGBA
internalFormat: GR_GL_BGRA8

desktop:
endian: RGBA
internalFormat: RGBA

src/gpu/gl/GrGLDefines.h

python skia.py -r release --test-type=tests --run-option '--match WritePixels' -d host -b release
python skia.py -r release --test-type=tests --run-option '--match WritePixels' -d BaytrailT2e0dca0243 -b release
</WritePixels>