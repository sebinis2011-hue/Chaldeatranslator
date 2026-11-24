#include <jni.h>
#include <llama.h>

#include <algorithm>
#include <atomic>
#include <cstdint>
#include <mutex>
#include <string>
#include <vector>

namespace {
std::mutex g_mutex;
llama_model * g_model = nullptr;
llama_context * g_context = nullptr;
std::atomic<bool> g_cancel{false};
bool g_backend_initialized = false;
int g_threads = 2;

void release_locked() {
    if (g_context) {
        llama_free(g_context);
        g_context = nullptr;
    }
    if (g_model) {
        llama_model_free(g_model);
        g_model = nullptr;
    }
}

void throw_java(JNIEnv * env, const char * message) {
    jclass cls = env->FindClass("java/lang/IllegalStateException");
    if (cls) env->ThrowNew(cls, message);
}

std::string to_utf8(JNIEnv * env, jstring value) {
    if (!value) return {};
    const char * chars = env->GetStringUTFChars(value, nullptr);
    if (!chars) return {};
    std::string result(chars);
    env->ReleaseStringUTFChars(value, chars);
    return result;
}

bool tokenize(const llama_vocab * vocab, const std::string & prompt, std::vector<llama_token> & tokens) {
    int32_t capacity = std::max<int32_t>(256, static_cast<int32_t>(prompt.size() / 2 + 32));
    tokens.resize(static_cast<size_t>(capacity));
    int32_t count = llama_tokenize(vocab, prompt.c_str(), static_cast<int32_t>(prompt.size()),
                                   tokens.data(), capacity, true, true);
    if (count < 0) {
        capacity = -count;
        tokens.resize(static_cast<size_t>(capacity));
        count = llama_tokenize(vocab, prompt.c_str(), static_cast<int32_t>(prompt.size()),
                               tokens.data(), capacity, true, false);
    }
    if (count <= 0) return false;
    tokens.resize(static_cast<size_t>(count));
    return true;
}
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_sebinis2011_chaldeatranslator_inference_LlamaCppInferenceEngine_nativeLoad(
        JNIEnv * env, jobject, jstring model_path, jint context_size, jint threads) {
    std::lock_guard<std::mutex> lock(g_mutex);
    release_locked();
    g_cancel.store(false);
    if (!g_backend_initialized) { llama_backend_init(); g_backend_initialized = true; }
    const std::string path = to_utf8(env, model_path);
    if (path.empty()) {
        throw_java(env, "La ruta del modelo está vacía.");
        return JNI_FALSE;
    }

    llama_model_params model_params = llama_model_default_params();
    model_params.n_gpu_layers = 0;
    model_params.use_mmap = true;
    model_params.use_mlock = false;
    g_model = llama_model_load_from_file(path.c_str(), model_params);
    if (!g_model) {
        throw_java(env, "llama.cpp no pudo abrir el GGUF. Comprueba que esté completo y sea compatible.");
        return JNI_FALSE;
    }

    llama_context_params context_params = llama_context_default_params();
    context_params.n_ctx = static_cast<uint32_t>(std::clamp(context_size, 512, 4096));
    context_params.n_batch = 128;
    context_params.n_ubatch = 128;
    g_threads = std::clamp(static_cast<int>(threads), 1, 6);
    context_params.n_threads = g_threads;
    context_params.n_threads_batch = g_threads;
    context_params.offload_kqv = false;
    g_context = llama_init_from_model(g_model, context_params);
    if (!g_context) {
        release_locked();
        throw_java(env, "No se pudo crear el contexto de inferencia. Reduce el contexto o libera memoria.");
        return JNI_FALSE;
    }
    return JNI_TRUE;
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_sebinis2011_chaldeatranslator_inference_LlamaCppInferenceEngine_nativeTranslate(
        JNIEnv * env, jobject, jstring prompt_value, jint max_tokens) {
    std::lock_guard<std::mutex> lock(g_mutex);
    if (!g_model || !g_context) {
        throw_java(env, "Primero debes cargar un modelo GGUF.");
        return nullptr;
    }
    g_cancel.store(false);
    const std::string prompt = to_utf8(env, prompt_value);
    if (prompt.empty()) {
        throw_java(env, "El prompt está vacío.");
        return nullptr;
    }

    const llama_vocab * vocab = llama_model_get_vocab(g_model);
    std::vector<llama_token> tokens;
    if (!tokenize(vocab, prompt, tokens)) {
        throw_java(env, "No se pudo tokenizar el texto de entrada.");
        return nullptr;
    }
    const uint32_t context_limit = llama_n_ctx(g_context);
    if (tokens.size() + 8 >= context_limit) {
        throw_java(env, "El texto supera el contexto disponible. Divide el fragmento y vuelve a intentarlo.");
        return nullptr;
    }
    llama_kv_self_clear(g_context);
    constexpr int32_t prompt_batch_size = 128;
    for (size_t offset = 0; offset < tokens.size(); offset += prompt_batch_size) {
        const size_t remaining = tokens.size() - offset;
        const int32_t count = static_cast<int32_t>(std::min<size_t>(remaining, prompt_batch_size));
        llama_batch prompt_batch = llama_batch_get_one(tokens.data() + offset, count);
        if (llama_decode(g_context, prompt_batch) != 0) {
            throw_java(env, "Falló la evaluación del prompt. Reduce la longitud del fragmento.");
            return nullptr;
        }
    }

    llama_sampler_chain_params sampler_params = llama_sampler_chain_default_params();
    llama_sampler * sampler = llama_sampler_chain_init(sampler_params);
    if (!sampler) {
        throw_java(env, "No se pudo crear el sampler.");
        return nullptr;
    }
    llama_sampler_chain_add(sampler, llama_sampler_init_top_k(40));
    llama_sampler_chain_add(sampler, llama_sampler_init_top_p(0.9f, 1));
    llama_sampler_chain_add(sampler, llama_sampler_init_temp(0.7f));
    llama_sampler_chain_add(sampler, llama_sampler_init_dist(LLAMA_DEFAULT_SEED));

    std::string output;
    const int available_tokens = static_cast<int>(context_limit - tokens.size());
    const int limit = std::clamp(std::min(static_cast<int>(max_tokens), available_tokens), 1, 1024);
    std::vector<char> piece(256);
    for (int i = 0; i < limit && !g_cancel.load(); ++i) {
        const llama_token token = llama_sampler_sample(sampler, g_context, -1);
        llama_sampler_accept(sampler, token);
        if (llama_vocab_is_eog(vocab, token)) break;
        int32_t n = llama_token_to_piece(vocab, token, piece.data(),
                                         static_cast<int32_t>(piece.size()), 0, false);
        if (n < 0) {
            piece.resize(static_cast<size_t>(-n));
            n = llama_token_to_piece(vocab, token, piece.data(),
                                     static_cast<int32_t>(piece.size()), 0, false);
        }
        if (n > 0) output.append(piece.data(), static_cast<size_t>(n));
        llama_token next = token;
        llama_batch decode_batch = llama_batch_get_one(&next, 1);
        if (llama_decode(g_context, decode_batch) != 0) break;
    }
    llama_sampler_free(sampler);
    return env->NewStringUTF(output.c_str());
}

extern "C" JNIEXPORT void JNICALL
Java_com_sebinis2011_chaldeatranslator_inference_LlamaCppInferenceEngine_nativeCancel(
        JNIEnv *, jobject) {
    g_cancel.store(true);
}

extern "C" JNIEXPORT void JNICALL
Java_com_sebinis2011_chaldeatranslator_inference_LlamaCppInferenceEngine_nativeUnload(
        JNIEnv *, jobject) {
    std::lock_guard<std::mutex> lock(g_mutex);
    g_cancel.store(true);
    release_locked();
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_sebinis2011_chaldeatranslator_inference_LlamaCppInferenceEngine_nativeRuntimeInfo(
        JNIEnv * env, jobject) {
    std::lock_guard<std::mutex> lock(g_mutex);
    std::string info = g_model && g_context
        ? "llama.cpp b5401 · CPU ARM64 · contexto " + std::to_string(llama_n_ctx(g_context)) +
          " · hilos " + std::to_string(g_threads)
        : "llama.cpp b5401 · modelo no cargado";
    return env->NewStringUTF(info.c_str());
}
