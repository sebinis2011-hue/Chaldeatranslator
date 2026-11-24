cmake_minimum_required(VERSION 3.22.1)
project(chaldea_llama LANGUAGES C CXX)

include(FetchContent)
set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_SERVER OFF CACHE BOOL "" FORCE)
set(LLAMA_CURL OFF CACHE BOOL "" FORCE)
set(GGML_NATIVE OFF CACHE BOOL "" FORCE)
set(GGML_OPENMP OFF CACHE BOOL "" FORCE)
set(GGML_LLAMAFILE OFF CACHE BOOL "" FORCE)
set(GGML_VULKAN OFF CACHE BOOL "" FORCE)
set(GGML_CPU_KLEIDIAI OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_COMMON OFF CACHE BOOL "" FORCE)

FetchContent_Declare(
    llama_cpp
    GIT_REPOSITORY https://github.com/ggml-org/llama.cpp.git
    GIT_TAG bc098c3cf0aac93e57e9bda9d95e2456acf88894
    GIT_SUBMODULES_RECURSE TRUE
)
FetchContent_MakeAvailable(llama_cpp)

add_library(chaldea_llama SHARED llama_jni.cpp)
target_compile_features(chaldea_llama PRIVATE cxx_std_17)
target_compile_options(chaldea_llama PRIVATE -fvisibility=hidden -Wall -Wextra)
target_link_libraries(chaldea_llama PRIVATE llama android log)
