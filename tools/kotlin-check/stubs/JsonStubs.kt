@file:Suppress("unused", "UNUSED_PARAMETER")

// A working org.json, small enough to read.
//
// Android bundles org.json; a plain JVM does not, so without this the AI
// pattern service could not be compiled off-device, let alone run. It is a real
// implementation rather than a no-op precisely because the things worth
// checking about that service - that the request body carries the right model
// and schema, and that the response parser skips thinking blocks - are only
// visible if the JSON actually round-trips.
package org.json

class JSONException(msg: String) : RuntimeException(msg)

class JSONObject {
    private val map = LinkedHashMap<String, Any?>()

    constructor()
    constructor(source: String) {
        val v = JsonParser(source).parseValue()
        if (v !is JSONObject) throw JSONException("not an object")
        map.putAll(v.entries())
    }

    internal fun entries(): Map<String, Any?> = map

    fun put(key: String, value: Any?): JSONObject { map[key] = value; return this }
    fun put(key: String, value: Int): JSONObject { map[key] = value; return this }
    fun put(key: String, value: Boolean): JSONObject { map[key] = value; return this }

    fun has(key: String): Boolean = map.containsKey(key)
    fun get(key: String): Any? = map[key] ?: throw JSONException("no such key: " + key)
    fun getString(key: String): String = get(key) as? String ?: throw JSONException(key + " is not a string")
    fun getJSONArray(key: String): JSONArray = get(key) as? JSONArray ?: throw JSONException(key + " is not an array")
    fun getJSONObject(key: String): JSONObject = get(key) as? JSONObject ?: throw JSONException(key + " is not an object")

    fun optString(key: String, fallback: String = ""): String = map[key] as? String ?: fallback
    fun optInt(key: String, fallback: Int = 0): Int = (map[key] as? Number)?.toInt() ?: fallback
    fun optJSONArray(key: String): JSONArray? = map[key] as? JSONArray
    fun optJSONObject(key: String): JSONObject? = map[key] as? JSONObject

    override fun toString(): String =
        map.entries.joinToString(",", "{", "}") { (k, v) -> quote(k) + ":" + render(v) }
}

class JSONArray {
    private val list = ArrayList<Any?>()

    constructor()
    constructor(from: Collection<*>) { list.addAll(from) }
    internal constructor(marker: Boolean, items: List<Any?>) { list.addAll(items) }

    fun put(value: Any?): JSONArray { list.add(value); return this }
    fun length(): Int = list.size
    fun get(i: Int): Any? = list[i]
    fun getString(i: Int): String = list[i] as? String ?: throw JSONException("not a string")
    fun getJSONObject(i: Int): JSONObject = list[i] as? JSONObject ?: throw JSONException("not an object")
    fun optJSONObject(i: Int): JSONObject? = list.getOrNull(i) as? JSONObject

    override fun toString(): String = list.joinToString(",", "[", "]") { render(it) }
}

private fun quote(s: String): String {
    val sb = StringBuilder("\"")
    for (c in s) when (c) {
        '"'  -> sb.append("\\\"")
        '\\' -> sb.append("\\\\")
        '\n' -> sb.append("\\n")
        '\r' -> sb.append("\\r")
        '\t' -> sb.append("\\t")
        else -> if (c < ' ') sb.append("\\u%04x".format(c.code)) else sb.append(c)
    }
    return sb.append('"').toString()
}

private fun render(v: Any?): String = when (v) {
    null -> "null"
    is String -> quote(v)
    is Boolean, is Number, is JSONObject, is JSONArray -> v.toString()
    else -> quote(v.toString())
}

private class JsonParser(private val src: String) {
    private var i = 0
    private fun ws() { while (i < src.length && src[i].isWhitespace()) i++ }

    fun parseValue(): Any? {
        ws()
        if (i >= src.length) throw JSONException("unexpected end")
        return when (src[i]) {
            '{'  -> parseObject()
            '['  -> parseArray()
            '"'  -> parseString()
            't'  -> { expect("true"); true }
            'f'  -> { expect("false"); false }
            'n'  -> { expect("null"); null }
            else -> parseNumber()
        }
    }

    private fun expect(word: String) {
        if (!src.startsWith(word, i)) throw JSONException("expected " + word)
        i += word.length
    }

    private fun parseObject(): JSONObject {
        val o = JSONObject(); i++
        ws()
        if (i < src.length && src[i] == '}') { i++; return o }
        while (true) {
            ws()
            val k = parseString()
            ws()
            if (src[i] != ':') throw JSONException("expected colon")
            i++
            o.put(k, parseValue())
            ws()
            when {
                i < src.length && src[i] == ',' -> i++
                i < src.length && src[i] == '}' -> { i++; return o }
                else -> throw JSONException("bad object")
            }
        }
    }

    private fun parseArray(): JSONArray {
        val items = ArrayList<Any?>(); i++
        ws()
        if (i < src.length && src[i] == ']') { i++; return JSONArray(true, items) }
        while (true) {
            items.add(parseValue())
            ws()
            when {
                i < src.length && src[i] == ',' -> i++
                i < src.length && src[i] == ']' -> { i++; return JSONArray(true, items) }
                else -> throw JSONException("bad array")
            }
        }
    }

    private fun parseString(): String {
        if (src[i] != '"') throw JSONException("expected string")
        i++
        val sb = StringBuilder()
        while (src[i] != '"') {
            if (src[i] == '\\') {
                i++
                when (src[i]) {
                    'n'  -> sb.append('\n')
                    'r'  -> sb.append('\r')
                    't'  -> sb.append('\t')
                    'b'  -> sb.append('\b')
                    'f'  -> sb.append(12.toChar())
                    'u'  -> { sb.append(src.substring(i + 1, i + 5).toInt(16).toChar()); i += 4 }
                    else -> sb.append(src[i])
                }
            } else sb.append(src[i])
            i++
        }
        i++
        return sb.toString()
    }

    private fun parseNumber(): Any {
        val start = i
        while (i < src.length && (src[i].isDigit() || src[i] in "-+.eE")) i++
        val t = src.substring(start, i)
        return t.toIntOrNull() ?: t.toLongOrNull() ?: t.toDouble()
    }
}
