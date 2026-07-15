package com.beadsnap.app

import android.app.Application
import com.beadsnap.app.data.store.PatternStore
import com.beadsnap.app.services.KeystoreHelper

class BeadSnapApp : Application() {
    override fun onCreate() {
        super.onCreate()
        KeystoreHelper.init(this)
        // Warm up PatternStore — starts loading user patterns in background
        PatternStore.getInstance(this)
    }
}
