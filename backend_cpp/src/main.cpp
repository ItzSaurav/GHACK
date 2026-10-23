#include "groq_client.hpp"
#include "language_detector.hpp"

#include <httplib.h>
#include <json.hpp>

#include <csignal>
#include <cstdlib>
#include <iostream>
#include <memory>
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

    // 2. Chat / Conversational endpoint
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
