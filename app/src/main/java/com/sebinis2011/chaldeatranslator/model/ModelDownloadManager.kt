package com.sebinis2011.chaldeatranslator.model
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import java.util.Locale
import android.os.StatFs
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.withContext
import kotlin.coroutines.coroutineContext

data class ModelSpec(val id:String,val name:String,val fileName:String,val downloadUrl:String,val sizeBytes:Long,val sha256:String,val revision:String)
object ModelCatalog {
 val initial=ModelSpec("qwen3-1.7b-q4_k_m-bartowski","Qwen3 1.7B · Q4_K_M","Qwen_Qwen3-1.7B-Q4_K_M.gguf",
 "https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/dcb19155b962dbb6389f4691a982043a8e651022/Qwen_Qwen3-1.7B-Q4_K_M.gguf",
 1_282_439_584L,"72c5c3cb38fa32d5256e2fe30d03e7a64c6c79e668ad84057e3bd66e250b24fb","dcb19155b962dbb6389f4691a982043a8e651022")
}
class ModelDownloadManager(private val modelDirectory:File) {
 suspend fun download(model:ModelSpec,onProgress:(Long,Long)->Unit):File=withContext(Dispatchers.IO) {
  require(model.downloadUrl.startsWith("https://huggingface.co/"))
  require(model.sizeBytes>0 && model.sha256.matches(Regex("[a-fA-F0-9]{64}")))
  modelDirectory.mkdirs()
  val target=File(modelDirectory,model.fileName)
  if(target.isFile && target.length()==model.sizeBytes && sha256(target).equals(model.sha256,true)) return@withContext target
  val part=File(modelDirectory,model.fileName+".part")
  val etagFile=File(modelDirectory,model.fileName+".etag")
  val storage = StatFs(modelDirectory.absolutePath)
  require(storage.availableBytes >= model.sizeBytes + 128L * 1024L * 1024L) { "No hay espacio libre suficiente para descargar el GGUF con margen." }
  val savedEtag = etagFile.takeIf { it.isFile }?.readText()?.takeIf { it.isNotBlank() }
  var offset=part.takeIf{it.isFile}?.length()?:0L
  if(offset>model.sizeBytes){part.delete();etagFile.delete();offset=0L}
  var connection:HttpURLConnection?=null
  try {
   connection=(URL(model.downloadUrl).openConnection() as HttpURLConnection).apply {
    instanceFollowRedirects=true;connectTimeout=20_000;readTimeout=60_000
    setRequestProperty("Accept-Encoding","identity")
    if(offset>0L){setRequestProperty("Range","bytes=$offset-");savedEtag?.let{setRequestProperty("If-Range",it)}}
   }
   val status=connection.responseCode
   val host=connection.url.host.lowercase(Locale.ROOT)
   require(host=="huggingface.co"||host.endsWith(".huggingface.co")||host.endsWith(".xethub.hf.co")){"Redirección a host no autorizado."}
   val append=offset>0L && status==HttpURLConnection.HTTP_PARTIAL
   if(offset>0L&&!append){part.delete();etagFile.delete();offset=0L}
   require(status==HttpURLConnection.HTTP_OK||append){"Error HTTP $status al descargar."}
   val responseEtag=connection.getHeaderField("ETag")
   if(append && savedEtag!=null && responseEtag!=savedEtag) { part.delete(); etagFile.delete(); throw SecurityException("El ETag cambió durante la reanudación; se descartó el parcial.") }
   responseEtag?.let{etagFile.writeText(it)}
   val expectedRemaining=model.sizeBytes-offset
   val declared=connection.getHeaderFieldLong("Content-Length",-1L)
   require(declared<0L||declared==expectedRemaining){"Longitud HTTP no coincide con catálogo."}
   var count=offset
   connection.inputStream.use{input->
    FileOutputStream(part,append).buffered().use{output->
     val buffer=ByteArray(131072)
     while(true){coroutineContext.ensureActive();val n=input.read(buffer);if(n<0)break
      count+=n;require(count<=model.sizeBytes){"El servidor envió más bytes de los esperados."}
      output.write(buffer,0,n);onProgress(count,model.sizeBytes)
     };output.flush()
    }
   }
   require(count==model.sizeBytes&&part.length()==model.sizeBytes){"Descarga incompleta: $count de ${model.sizeBytes} bytes."}
   if(!sha256(part).equals(model.sha256,true)){part.delete();etagFile.delete();throw SecurityException("SHA-256 incorrecto; GGUF rechazado.")}
   try{java.nio.file.Files.move(part.toPath(),target.toPath(),java.nio.file.StandardCopyOption.REPLACE_EXISTING,java.nio.file.StandardCopyOption.ATOMIC_MOVE)}
   catch(_:Exception){if(!part.renameTo(target))throw IllegalStateException("No se pudo activar el modelo verificado.")}
   etagFile.delete();target
  } finally {connection?.disconnect()}
 }
 private fun sha256(file:File):String {
  val digest=MessageDigest.getInstance("SHA-256")
  FileInputStream(file).use{input->val buffer=ByteArray(131072);while(true){val n=input.read(buffer);if(n<0)break;digest.update(buffer,0,n)}}
  return digest.digest().joinToString(""){"%02x".format(it)}
 }
}