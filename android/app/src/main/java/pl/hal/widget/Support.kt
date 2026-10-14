package pl.hal.widget

import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.SharedPreferences

/** Proste przechowywanie konfiguracji (URL panelu). */
object Prefs {
    private const val FILE = "hal_widget"

    private fun prefs(ctx: Context): SharedPreferences =
        ctx.getSharedPreferences(FILE, Context.MODE_PRIVATE)

    fun url(ctx: Context): String = prefs(ctx).getString("url", "") ?: ""
    fun setUrl(ctx: Context, value: String) {
        prefs(ctx).edit().putString("url", value).apply()
    }
}

/**
 * Rejestrowany DYNAMICZNIE w OverlayService (statyczna rejestracja
 * SCREEN_ON/SCREEN_OFF w manifeście nie działa na Androidzie 8+).
 */
class ScreenReceiver(
    private val onScreenOff: () -> Unit,
    private val onScreenOn: () -> Unit
) : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        when (intent.action) {
            Intent.ACTION_SCREEN_OFF -> onScreenOff()
            Intent.ACTION_SCREEN_ON -> onScreenOn()
        }
    }

    companion object {
        fun filter(): IntentFilter = IntentFilter().apply {
            addAction(Intent.ACTION_SCREEN_OFF)
            addAction(Intent.ACTION_SCREEN_ON)
        }
    }
}

/** Autostart usługi po restarcie telefonu. */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (Intent.ACTION_BOOT_COMPLETED == intent.action) {
            context.startForegroundService(Intent(context, OverlayService::class.java))
        }
    }
}
