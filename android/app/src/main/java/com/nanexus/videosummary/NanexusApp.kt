package com.nanexus.videosummary

import android.app.Application
import com.nanexus.videosummary.data.repo.NanexusRepository
import com.nanexus.videosummary.data.settings.AppSettings

class NanexusApp : Application() {
    lateinit var repository: NanexusRepository
        private set

    override fun onCreate() {
        super.onCreate()
        repository = NanexusRepository(AppSettings(this))
    }
}
