package com.gemma.chat.data

import com.gemma.chat.model.OllamaConfig
import com.google.gson.Gson
import com.google.gson.JsonParser
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.flowOn
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

class OllamaRepository(private var config: OllamaConfig) {
    
    private var apiService: OllamaApiService
    private val gson = Gson()
    private val jsonParser = JsonParser()
    
    private val client = OkHttpClient.Builder()
        .connectTimeout(60, TimeUnit.SECONDS)
        .readTimeout(300, TimeUnit.SECONDS)
        .writeTimeout(60, TimeUnit.SECONDS)
        .addInterceptor(HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        })
        .build()
    
    init {
        apiService = createApiService(config.baseUrl)
    }
    
    private fun createApiService(baseUrl: String): OllamaApiService {
        val url = if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/"
        return Retrofit.Builder()
            .baseUrl(url)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(OllamaApiService::class.java)
    }
    
    fun updateConfig(newConfig: OllamaConfig) {
        config = newConfig
        apiService = createApiService(newConfig.baseUrl)
    }
    
    fun getConfig(): OllamaConfig = config
    
    fun chat(messages: List<OllamaChatMessage>): Flow<String> = callbackFlow {
        try {
            val request = OllamaChatRequest(
                model = config.model,
                messages = messages,
                stream = true,
                options = OllamaOptions(
                    temperature = config.temperature,
                    numPredict = config.maxTokens
                )
            )
            
            val response = apiService.chat(request)
            
            if (response.isSuccessful) {
                val body = response.body()
                if (body != null) {
                    val source = body.source()
                    val buffer = okio.Buffer()
                    
                    while (!source.exhausted()) {
                        val bytesRead = source.read(buffer, 8192)
                        if (bytesRead == -1L) break
                        
                        val lines = buffer.readUtf8().split("\n")
                        for (line in lines) {
                            if (line.isNotBlank()) {
                                try {
                                    val jsonElement = jsonParser.parse(line)
                                    val jsonObject = jsonElement.asJsonObject
                                    
                                    if (jsonObject.has("message")) {
                                        val message = jsonObject.getAsJsonObject("message")
                                        val content = message.get("content")?.asString ?: ""
                                        if (content.isNotEmpty()) {
                                            trySend(content)
                                        }
                                    }
                                    
                                    if (jsonObject.has("done") && jsonObject.get("done").asBoolean) {
                                        close()
                                        return@callbackFlow
                                    }
                                } catch (e: Exception) {
                                    // Ignore malformed JSON lines
                                }
                            }
                        }
                    }
                }
                close()
            } else {
                val errorBody = response.errorBody()?.string() ?: "Unknown error"
                close(Exception("API Error: ${response.code()} - $errorBody"))
            }
        } catch (e: Exception) {
            close(e)
        }
        
        awaitClose { }
    }.flowOn(Dispatchers.IO)
    
    fun getAvailableModels(): Result<List<OllamaModel>> {
        return try {
            val response = apiService.getModels()
            if (response.isSuccessful) {
                Result.success(response.body()?.models ?: emptyList())
            } else {
                Result.failure(Exception("Failed to fetch models: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    fun testConnection(): Result<Boolean> {
        return try {
            val response = apiService.getModels()
            Result.success(response.isSuccessful)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
