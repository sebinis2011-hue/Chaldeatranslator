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
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { ChaldeaApp() }
    }
}

@Composable
private fun ChaldeaApp() {
    var source by remember { mutableStateOf("") }
    var status by remember { mutableStateOf("Motor IA todavía no integrado.") }

    MaterialTheme {
        Surface(modifier = Modifier.fillMaxSize()) {
            Column(
                modifier = Modifier.fillMaxSize().padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                Text("ChaldeaTranslator", style = MaterialTheme.typography.headlineMedium)
                Text("Aplicación Android nativa · versión de desarrollo")
                OutlinedTextField(
                    value = source,
                    onValueChange = { source = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Texto original") },
                    minLines = 5
                )
                Button(
                    onClick = {
                        status = if (source.isBlank()) {
                            "Escribe un texto antes de traducir."
                        } else {
                            "El texto está listo. Falta integrar y cargar el modelo GGUF."
                        }
                    },
                    modifier = Modifier.fillMaxWidth()
                ) { Text("Preparar traducción") }
                Text(status, style = MaterialTheme.typography.bodyMedium)
                Text(
                    "El motor actual no realiza inferencia todavía. Esta pantalla no simula una traducción.",
                    style = MaterialTheme.typography.bodySmall
                )
            }
        }
    }
}
