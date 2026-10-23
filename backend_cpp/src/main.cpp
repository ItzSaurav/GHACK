#include "groq_client.hpp"
#include "language_detector.hpp"

#include <httplib.h>
#include <json.hpp>

#include <csignal>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

using json = nlohmann::json;
using namespace voicebot;

static std::unique_ptr<httplib::Server> g_server;

void signal_handler(int sig) {
    std::cout << "\nReceived signal " << sig << ", shutting down C++ voicebot server..." << std::endl;
    if (g_server) {
        g_server->stop();
    }
}

int main(int argc, char* argv[]) {
    std::signal(SIGINT, signal_handler);
    std::signal(SIGTERM, signal_handler);

    int port = 8000;
    if (const char* env_p = std::getenv("PORT")) {
        try {
            port = std::stoi(env_p);
        } catch (...) {}
    }
    std::string host = "0.0.0.0";
    if (const char* env_h = std::getenv("HOST")) {
        host = env_h;
    }

    std::cout << "========================================================\n";
    std::cout << "Sahaay Multilingual C++ Voicebot Server\n";
    std::cout << "Languages: English, Hindi, Gujarati, Marathi\n";
    std::cout << "Listening on: http://" << host << ":" << port << "\n";
    std::cout << "========================================================\n" << std::endl;

    GroqClient groq;
    std::cout << "Groq API Status: "
              << (groq.is_available() ? "Configured & Active" : "Key Not Found (Offline Fallback Active)")
              << std::endl;

    g_server = std::make_unique<httplib::Server>();

    // CORS Middleware
    g_server->set_pre_routing_handler([](const httplib::Request& req, httplib::Response& res) {
        res.set_header("Access-Control-Allow-Origin", "*");
        res.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE");
        res.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With");
        if (req.method == "OPTIONS") {
            res.status = 204;
            return httplib::Server::HandlerResponse::Handled;
        }
        return httplib::Server::HandlerResponse::Unhandled;
    });

    // 1. Health check endpoint
    g_server->Get("/api/health", [&groq](const httplib::Request&, httplib::Response& res) {
        groq.reload_env();
        json response = {
            {"status", "healthy"},
            {"engine", "cpp-voicebot-core"},
            {"groq_available", groq.is_available()},
            {"languages", json::array({
                {{"code", "en"}, {"name", "English"}, {"bcp47", "en-IN"}},
                {{"code", "hi"}, {"name", "हिन्दी (Hindi)"}, {"bcp47", "hi-IN"}},
                {{"code", "gu"}, {"name", "ગુજરાતી (Gujarati)"}, {"bcp47", "gu-IN"}},
                {{"code", "mr"}, {"name", "मराठी (Marathi)"}, {"bcp47", "mr-IN"}}
            })}
        };
        res.set_content(response.dump(), "application/json");
    });

    // 2. Neural Audio TTS Endpoint (Edge-TTS via local worker with file cache)
    auto handle_tts = [](const std::string& text, const std::string& lang, httplib::Response& res) {
        if (text.empty()) {
            json err = {{"success", false}, {"error", "Text parameter is required"}};
            res.status = 400;
            res.set_content(err.dump(), "application/json");
            return;
        }

        std::string effective_lang = lang;
        if (effective_lang.empty() || effective_lang == "auto") {
            effective_lang = LanguageDetector::detect(text).code;
        }

        size_t hash_val = std::hash<std::string>{}(text + "_" + effective_lang);
        std::string cache_dir = "/tmp/voicebot_tts_cache";
        std::error_code ec;
        std::filesystem::create_directories(cache_dir, ec);

        std::string mp3_path = cache_dir + "/" + std::to_string(hash_val) + ".mp3";
        std::string txt_path = cache_dir + "/" + std::to_string(hash_val) + ".txt";

        // Check if cached mp3 exists
        if (std::filesystem::exists(mp3_path)) {
            auto file_sz = std::filesystem::file_size(mp3_path, ec);
            if (file_sz > 500) {
                std::ifstream check_file(mp3_path, std::ios::binary);
                if (check_file.is_open()) {
                    std::ostringstream ss;
                    ss << check_file.rdbuf();
                    std::string content = ss.str();
                    res.set_header("Content-Type", "audio/mpeg");
                    res.set_header("Cache-Control", "public, max-age=86400");
                    res.set_content(content, "audio/mpeg");
                    return;
                }
            } else {
                std::filesystem::remove(mp3_path, ec);
            }
        }

        // Generate via scripts/tts_worker.py
        {
            std::ofstream txt_file(txt_path);
            txt_file << text;
        }

        std::string py_bin = "python3";
        if (std::filesystem::exists(".venv/bin/python")) {
            py_bin = ".venv/bin/python";
        } else if (std::filesystem::exists("/home/saurav/Documents/GHACK/.venv/bin/python")) {
            py_bin = "/home/saurav/Documents/GHACK/.venv/bin/python";
        } else if (const char* venv_p = std::getenv("VIRTUAL_ENV")) {
            py_bin = std::string(venv_p) + "/bin/python";
        }

        std::string script_path = "scripts/tts_worker.py";
        if (!std::filesystem::exists(script_path) && std::filesystem::exists("/home/saurav/Documents/GHACK/scripts/tts_worker.py")) {
            script_path = "/home/saurav/Documents/GHACK/scripts/tts_worker.py";
        }

        std::string cmd = py_bin + " " + script_path + " \"" + txt_path + "\" \"" + effective_lang + "\" \"" + mp3_path + "\" >/dev/null 2>&1";
        int ret = std::system(cmd.c_str());
        (void)ret;
        std::filesystem::remove(txt_path, ec);

        if (std::filesystem::exists(mp3_path)) {
            auto sz = std::filesystem::file_size(mp3_path, ec);
            if (sz > 100) {
                std::ifstream result_file(mp3_path, std::ios::binary);
                if (result_file.is_open()) {
                    std::ostringstream ss;
                    ss << result_file.rdbuf();
                    std::string content = ss.str();
                    res.set_header("Content-Type", "audio/mpeg");
                    res.set_header("Cache-Control", "public, max-age=86400");
                    res.set_content(content, "audio/mpeg");
                    return;
                }
            } else {
                std::filesystem::remove(mp3_path, ec);
            }
        }

        json err = {{"success", false}, {"error", "Failed to synthesize neural audio"}};
        res.status = 500;
        res.set_content(err.dump(), "application/json");
    };

    g_server->Get("/api/tts", [&handle_tts](const httplib::Request& req, httplib::Response& res) {
        std::string text = req.get_param_value("text");
        std::string lang = req.get_param_value("lang");
        handle_tts(text, lang, res);
    });

    g_server->Post("/api/tts", [&handle_tts](const httplib::Request& req, httplib::Response& res) {
        try {
            json body = json::parse(req.body);
            std::string text = body.value("text", "");
            std::string lang = body.contains("language") ? body.value("language", "hi") : body.value("lang", "hi");
            handle_tts(text, lang, res);
        } catch (...) {
            json err = {{"success", false}, {"error", "Invalid JSON payload"}};
            res.status = 400;
            res.set_content(err.dump(), "application/json");
        }
    });

    // 3. Chat / Conversational endpoint
    g_server->Post("/api/chat", [&groq](const httplib::Request& req, httplib::Response& res) {
        groq.reload_env();
        try {
            json body = json::parse(req.body);
            std::string message = body.value("message", "");
            std::string explicit_lang = body.value("language", "auto");

            std::vector<ChatMessage> history;
            if (body.contains("history") && body["history"].is_array()) {
                for (const auto& item : body["history"]) {
                    history.push_back({
                        item.value("role", "user"),
                        item.value("content", "")
                    });
                }
            }

            if (!message.empty()) {
                history.push_back({"user", message});
            }

            if (history.empty()) {
                json err = {{"success", false}, {"error", "Message or history is required"}};
                res.status = 400;
                res.set_content(err.dump(), "application/json");
                return;
            }

            ChatResult chat_res = groq.chat(history, explicit_lang);

            json output = {
                {"success", chat_res.success},
                {"reply", chat_res.reply},
                {"detected_language", chat_res.language_info.code},
                {"language_name", chat_res.language_info.display_name},
                {"bcp47", chat_res.language_info.bcp47},
                {"model", chat_res.model}
            };

            if (!chat_res.error.empty()) {
                output["error"] = chat_res.error;
            }

            res.set_content(output.dump(), "application/json");
        } catch (const std::exception& e) {
            json err = {{"success", false}, {"error", std::string("Invalid JSON payload: ") + e.what()}};
            res.status = 400;
            res.set_content(err.dump(), "application/json");
        }
    });

    // 3. Audio transcription endpoint
    g_server->Post("/api/transcribe", [&groq](const httplib::Request& req, httplib::Response& res) {
        groq.reload_env();
        std::string audio_bytes;
        std::string filename = "audio.webm";

        if (req.form.has_file("file")) {
            auto file = req.form.get_file("file");
            audio_bytes = file.content;
            if (!file.filename.empty()) filename = file.filename;
        } else if (req.form.has_file("audio")) {
            auto file = req.form.get_file("audio");
            audio_bytes = file.content;
            if (!file.filename.empty()) filename = file.filename;
        } else if (!req.body.empty()) {
            audio_bytes = req.body;
        }

        if (audio_bytes.empty()) {
            json err = {{"success", false}, {"error", "No audio file provided in request"}};
            res.status = 400;
            res.set_content(err.dump(), "application/json");
            return;
        }

        TranscriptionResult tr = groq.transcribe(audio_bytes, filename);
        if (!tr.success) {
            json err = {
                {"success", false},
                {"error", tr.error},
                {"text", ""}
            };
            res.status = 500;
            res.set_content(err.dump(), "application/json");
            return;
        }

        json output = {
            {"success", true},
            {"text", tr.text},
            {"detected_language", tr.language_info.code},
            {"language_name", tr.language_info.display_name},
            {"bcp47", tr.language_info.bcp47},
            {"duration", tr.duration}
        };
        res.set_content(output.dump(), "application/json");
    });

    // 4. Voice Interaction (transcribe audio + get conversational answer)
    g_server->Post("/api/voice/interact", [&groq](const httplib::Request& req, httplib::Response& res) {
        groq.reload_env();
        std::string audio_bytes;
        std::string filename = "audio.webm";
        std::string history_json_str;

        if (req.form.has_file("audio")) {
            auto file = req.form.get_file("audio");
            audio_bytes = file.content;
            if (!file.filename.empty()) filename = file.filename;
        } else if (req.form.has_file("file")) {
            auto file = req.form.get_file("file");
            audio_bytes = file.content;
            if (!file.filename.empty()) filename = file.filename;
        } else if (!req.body.empty()) {
            audio_bytes = req.body;
        }

        if (req.form.has_field("history")) {
            history_json_str = req.form.get_field("history");
        }

        if (audio_bytes.empty()) {
            json err = {{"success", false}, {"error", "No audio file uploaded"}};
            res.status = 400;
            res.set_content(err.dump(), "application/json");
            return;
        }

        TranscriptionResult tr = groq.transcribe(audio_bytes, filename);
        if (!tr.success) {
            json err = {
                {"success", false},
                {"error", tr.error},
                {"reply", "Could not transcribe audio. Please check your microphone or try again."}
            };
            res.status = 500;
            res.set_content(err.dump(), "application/json");
            return;
        }

        std::vector<ChatMessage> history;
        if (!history_json_str.empty()) {
            try {
                json hj = json::parse(history_json_str);
                if (hj.is_array()) {
                    for (const auto& item : hj) {
                        history.push_back({
                            item.value("role", "user"),
                            item.value("content", "")
                        });
                    }
                }
            } catch (...) {}
        }

        history.push_back({"user", tr.text});

        ChatResult cr = groq.chat(history, tr.language_info.code);

        json output = {
            {"success", true},
            {"transcription", tr.text},
            {"reply", cr.reply},
            {"detected_language", tr.language_info.code},
            {"language_name", tr.language_info.display_name},
            {"bcp47", tr.language_info.bcp47},
            {"model", cr.model}
        };

        res.set_content(output.dump(), "application/json");
    });

    if (!g_server->listen(host, port)) {
        std::cerr << "Failed to bind to " << host << ":" << port << std::endl;
        return 1;
    }

    return 0;
}
