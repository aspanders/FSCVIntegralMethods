@file:Suppress("unused", "UNUSED_PARAMETER")

// Enough of OkHttp to build a request and hand back a canned response.
//
// Nothing here goes near a socket. The point is that a request built by the app
// can be INSPECTED - `Request.bodyText` and `Request.headers` are the whole
// reason this exists - so a harness can assert which model, which max_tokens
// and which schema the app actually puts on the wire, rather than trusting that
// the code reads correctly.
package okhttp3

import java.io.IOException
import java.util.concurrent.TimeUnit

// The extensions live in companion objects in real OkHttp, and the app imports
// them by that path (okhttp3.MediaType.Companion.toMediaType). Declaring them
// top-level here would compile in the stub and fail against the real library.
class MediaType(val value: String) {
    companion object {
        fun String.toMediaType(): MediaType = MediaType(this)
    }
}

class RequestBody(val text: String, val contentType: MediaType?) {
    companion object {
        fun String.toRequestBody(contentType: MediaType? = null): RequestBody =
            RequestBody(this, contentType)
    }
}

class Request private constructor(
    val url: String,
    val bodyText: String,
    val headers: Map<String, String>
) {
    class Builder {
        private var url: String = ""
        private var body: RequestBody? = null
        private val headers = LinkedHashMap<String, String>()
        fun url(u: String): Builder { url = u; return this }
        fun post(b: RequestBody): Builder { body = b; return this }
        fun header(k: String, v: String): Builder { headers[k] = v; return this }
        fun build(): Request = Request(url, body?.text ?: "", headers)
    }
}

/**
 * [string] is declared @Throws(IOException) in real OkHttp: it reads the rest
 * of the body off the socket, so a dropped link or an expired read timeout
 * throws HERE, inside the callback, rather than at enqueue time. [failWith]
 * lets a harness reproduce that - it is the case a callback is most likely to
 * get wrong, because on a fast local connection it never happens.
 */
class ResponseBody(private val text: String, private val failWith: Throwable? = null) {
    fun string(): String = failWith?.let { throw it } ?: text
}

class Response(
    val code: Int = 200,
    private val text: String = "",
    // Throwable, not IOException. string() is DECLARED @Throws(IOException),
    // but it also allocates a buffer the size of the whole body, so an
    // OutOfMemoryError comes out of it too - and an Error is exactly what a
    // `catch (e: Exception)` in a callback lets escape.
    private val bodyFailure: Throwable? = null
) : java.io.Closeable {
    val isSuccessful: Boolean get() = code in 200..299
    val body: ResponseBody? get() = ResponseBody(text, bodyFailure)
    override fun close() {}
}

interface Callback {
    fun onFailure(call: Call, e: IOException)
    fun onResponse(call: Call, response: Response)
}

/**
 * A call that replays whatever [OkHttpClient.nextResponse] was primed with.
 * The request stays reachable as [request] so a test can look at what would
 * have been sent.
 */
class Call(val request: Request, private val canned: Response?, private val failure: IOException?) {
    private var cancelled = false
    fun cancel() { cancelled = true }
    fun isCanceled(): Boolean = cancelled
    fun enqueue(cb: Callback) {
        when {
            cancelled -> {}
            failure != null -> cb.onFailure(this, failure)
            // Real OkHttp catches whatever onResponse throws, logs
            // "Callback failure for ...", and does NOT then call onFailure -
            // by the time onResponse runs it has already set signalledCallback.
            // So a handler that lets a throw escape simply never resumes its
            // continuation, and the caller waits forever. Swallowing it here
            // the same way is what lets a harness SEE that hang instead of
            // getting a tidy exception the real library would never deliver.
            else -> try {
                cb.onResponse(this, canned ?: Response(200, ""))
            } catch (t: Throwable) {
                lastCallbackFailure = t
            }
        }
    }

    /** What the callback threw, if it threw. Nothing else is told. */
    var lastCallbackFailure: Throwable? = null
        private set
}

class OkHttpClient private constructor() {
    /** Primed by the harness; the next enqueue replays it. */
    var nextResponse: Response? = null
    var nextFailure: IOException? = null

    class Builder {
        fun connectTimeout(t: Long, u: TimeUnit): Builder = this
        fun readTimeout(t: Long, u: TimeUnit): Builder = this
        fun build(): OkHttpClient = OkHttpClient()
    }

    fun newCall(r: Request): Call = Call(r, nextResponse, nextFailure)
}
