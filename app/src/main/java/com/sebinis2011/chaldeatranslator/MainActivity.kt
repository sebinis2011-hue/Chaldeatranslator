package com.sebinis2011.chaldeatranslator

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.sebinis2011.chaldeatranslator.inference.LlamaCppInferenceEngine
import com.sebinis2011.chaldeatranslator.model.ModelCatalog
import com.sebinis2011.chaldeatranslator.model.ModelDownloadManager
import java.io.File
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { ChaldeaApp() }
    }
}

@Composable
private fun ChaldeaApp() {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val model = ModelCatalog.initial
    val modelDirectory = remember { File(context.filesDir, "models") }
    val downloader = remember { ModelDownloadManager(modelDirectory) }
    val engine = remember { LlamaCppInferenceEngine() }

    var source by remember { mutableStateOf("") }
    var translated by remember { mutableStateOf("") }
    var status by remember { mutableStateOf("Modelo aún no instalado. La descarga requiere aproximadamente 1.28 GB.") }
    var busy by remember { mutableStateOf(false) }
    var modelReady by remember { mutableStateOf(false) }
    var downloaded by remember { mutableLongStateOf(0L) }
    var total by remember { mutableLongStateOf(model.sizeBytes) }

    MaterialTheme {
        Surface(modifier = Modifier.fillMaxSize()) {
            Column(
                modifier = Modifier.fillMaxSize().padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Text("ChaldeaTranslator", style = MaterialTheme.typography.headlineMedium)
                Text("Inferencia local · llama.cpp · CPU ARM64")
                Text("Modelo: ${model.name}")
                Text("Tamaño: 1,282,439,584 bytes · SHA-256 verificado antes de activarlo")
                Button(
                    enabled = !busy && !modelReady,
                    onClick = {
                        busy = true
                        status = "Descargando modelo desde Hugging Face…"
                        scope.launch {
                            try {
                                val file = downloader.download(model) { current, size ->
                                    scope.launch {
                                        downloaded = current
                                        total = size
                                    }
                                }
                                status = "Archivo verificado. Cargando modelo en memoria…"
                                engine.loadModel(file)
                                modelReady = true
                                status = engine.runtimeInfo().detail ?: "Modelo cargado."
                            } catch (error: Exception) {
                                status = "No se pudo preparar el modelo: ${error.message ?: error.javaClass.simpleName}"
                            } finally {
                                busy = false
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth()
                ) { Text(if (busy) "Preparando modelo…" else "Descargar y cargar modelo (1.28 GB)") }

                if (busy) {
                    LinearProgressIndicator(
                        progress = { if (total > 0L) downloaded.toFloat() / total.toFloat() else 0f },
                        modifier = Modifier.fillMaxWidth()
                    )
                    Text("${downloaded / 1_000_000} MB / ${total / 1_000_000} MB")
                }

                OutlinedTextField(
                    value = source,
                    onValueChange = { source = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Texto original") },
                    minLines = 4
                )
                Button(
                    enabled = modelReady && !busy && source.isNotBlank(),
                    onClick = {
                        busy = true
                        translated = ""
                        status = "Generando traducción local…"
                        scope.launch {
                            try {
                                val prompt = buildString {
                                    append("<|im_start|>system\n")
                                    append("Eres ChaldeaTranslator, un traductor literario experto en Fate/TYPE-MOON. ")
                                    append("Traduce al español latino natural. Conserva nombres propios, términos del lore, ")
                                    append("habilidades, formato y voz de los personajes. No añadas explicaciones ni inventes contenido. ")
                                    append("Devuelve únicamente la traducción.\n<|im_end|>\n")
                                    append("<|im_start|>user\n")
                                    append(source)
                                    append("\n<|im_end|>\n<|im_start|>assistant\n")
                                }
                                translated = engine.translate(prompt, 512)
                                status = "Traducción generada localmente. Revisa terminología y contexto antes de usarla."
                            } catch (error: Exception) {
                                status = "Error de inferencia: ${error.message ?: error.javaClass.simpleName}"
                            } finally {
                                busy = false
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth()
                ) { Text("Traducir localmente") }

                if (busy && modelReady) {
                    Button(onClick = { scope.launch { engine.cancel() } }, modifier = Modifier.fillMaxWidth()) {
                        Text("Cancelar generación")
                    }
                }
                Text(status, style = MaterialTheme.typography.bodyMedium)
                if (translated.isNotBlank()) {
                    Text("Traducción", style = MaterialTheme.typography.titleMedium)
                    Text(translated, style = MaterialTheme.typography.bodyLarge)
                }
                Text(
                    "El GGUF se guarda en el almacenamiento privado de la app. La inferencia no envía el texto a servidores. " +
                        "La descarga requiere Internet; después puedes traducir sin conexión.",
                    style = MaterialTheme.typography.bodySmall
                )
            }
        }
    }
}
