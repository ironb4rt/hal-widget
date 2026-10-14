package pl.hal.widget

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView

/**
 * Ekran konfiguracji: URL treści + przyciski nadania uprawnienia overlay
 * i startu/zatrzymania pływającego okna.
 */
class MainActivity : Activity() {

    private lateinit var urlInput: EditText
    private lateinit var status: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val pad = (16 * resources.displayMetrics.density).toInt()
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(pad, pad, pad, pad)
        }

        layout.addView(TextView(this).apply { text = "Hal Widget — konfiguracja" })

        urlInput = EditText(this).apply {
            hint = "URL panelu treści"
            setText(Prefs.url(this@MainActivity))
        }
        layout.addView(urlInput)

        layout.addView(Button(this).apply {
            text = "Nadaj uprawnienie overlay"
            setOnClickListener {
                startActivity(
                    Intent(
                        Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        Uri.parse("package:$packageName")
                    )
                )
            }
        })

        layout.addView(Button(this).apply {
            text = "Start okna"
            setOnClickListener {
                Prefs.setUrl(this@MainActivity, urlInput.text.toString().trim())
                if (Settings.canDrawOverlays(this@MainActivity)) {
                    startForegroundService(Intent(this@MainActivity, OverlayService::class.java))
                    // Białe okno konfiguracji nie jest już potrzebne — zamykam je.
                    finish()
                } else {
                    status.text = "Najpierw nadaj uprawnienie overlay."
                }
            }
        })

        layout.addView(Button(this).apply {
            text = "Stop okna"
            setOnClickListener { stopService(Intent(this@MainActivity, OverlayService::class.java)) }
        })

        // Wbudowany panel z APK — działa bez serwera i bez sieci.
        layout.addView(Button(this).apply {
            text = "Użyj wbudowanego panelu"
            setOnClickListener {
                Prefs.setUrl(this@MainActivity, "")
                urlInput.setText("")
                status.text = "Ustawiono wbudowany panel (assets/panel/panel.html)."
            }
        })

        status = TextView(this)
        layout.addView(status)

        setContentView(layout)
    }
}
