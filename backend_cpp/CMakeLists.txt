cmake_minimum_required(VERSION 3.20)
project(VoicebotServer LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(CURL REQUIRED)
find_package(OpenSSL REQUIRED)
find_package(Threads REQUIRED)

include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CURL_INCLUDE_DIRS}
    ${OPENSSL_INCLUDE_DIR}
)

# Common library for language detection and groq client
add_library(voicebot_core STATIC
    src/language_detector.cpp
    src/groq_client.cpp
)

target_link_libraries(voicebot_core PUBLIC
    ${CURL_LIBRARIES}
    OpenSSL::SSL
    OpenSSL::Crypto
    Threads::Threads
)

# Server executable
add_executable(voicebot_server
    src/main.cpp
)

target_link_libraries(voicebot_server PRIVATE
    voicebot_core
)

# Tests executables
enable_testing()
add_executable(test_language_detector
    tests/test_language_detector.cpp
)
target_link_libraries(test_language_detector PRIVATE
    voicebot_core
)

add_executable(test_groq_client
    tests/test_groq_client.cpp
)
target_link_libraries(test_groq_client PRIVATE
    voicebot_core
)

add_test(NAME TestLanguageDetector COMMAND test_language_detector)
add_test(NAME TestGroqClient COMMAND test_groq_client)
