package pl.hal.widget

import android.annotation.SuppressLint
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.graphics.PixelFormat
import android.os.IBinder
import android.util.TypedValue
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.LinearLayout
import android.widget.TextView
import java.net.URLEncoder
import kotlin.math.abs

/**
 * Pływające okno (overlay) z WebView. Dyscyplina baterii:
 * - przy zgaszonym ekranie ScreenReceiver woła onPause()/onResume() na WebView,
 * - brak timera, brak pollingu w tej klasie,
 * - WebView renderuje wyłącznie, gdy okno widoczne i ekran włączony.
 */
class OverlayService : Service() {

    private lateinit var wm: WindowManager
    private var webView: WebView? = null
    private lateinit var layoutParams: WindowManager.LayoutParams
    private var screenReceiver: ScreenReceiver? = null

    override fun onBind(intent: Intent?): IBinder? = null

    @SuppressLint("SetJavaScriptEnabled", "ClickableViewAccessibility")
    override fun onCreate() {
        super.onCreate()
        startForeground()

        wm = getSystemService(WINDOW_SERVICE) as WindowManager

        webView = WebView(this).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            // Panel z assets/panel/panel.html czyta panel_data.json przez fetch().
            // Bez allowFileAccessFromFileURLs żądanie file:// jest blokowane (CORS),
            // a bez allowUniversalAccessFromFileURLs nie działa z file:// na Androidzie 10+.
            settings.allowFileAccess = true
            settings.allowContentAccess = true
            settings.allowFileAccessFromFileURLs = true
            settings.allowUniversalAccessFromFileURLs = true
            webViewClient = WebViewClient()
            setBackgroundColor(0xFF070B14.toInt())
            // Domyślnie wbudowany panel z APK; URL z konfiguracji go nadpisuje.
            // Prefiks "data:" = wbudowany panel + dane z podanego URL (?src=),
            // dzięki czemu surowce/wiadomości świeżą się bez rebuildu APK.
            val configured = Prefs.url(this@OverlayService)
            when {
                configured.startsWith("data:") ->
                    loadUrl("file:///android_asset/panel/panel.html?src=" +
                        URLEncoder.encode(configured.removePrefix("data:"), "UTF-8"))
                configured.isNotEmpty() -> loadUrl(configured)
                else -> loadUrl("file:///android_asset/panel/panel.html")
            }
        }

        layoutParams = WindowManager.LayoutParams(
            (340 * resources.displayMetrics.density).toInt(),
            (480 * resources.displayMetrics.density).toInt(),
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            // Okno jest fokusowalne — pole czatu w WebView samo otwiera
            // klawiaturę; koszt: klawisz wstecz trafia najpierw do okna.
            WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.END
            x = 24
            y = 24
        }

        // Pasek kontrolek: cofnięcie, skalowanie, minimalizacja, zamknięcie.
        val density = resources.displayMetrics.density
        var minimized = false
        var scale = 1f
        val controls = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.END or Gravity.CENTER_VERTICAL
            setBackgroundColor(0xF2070B14.toInt())
            setPadding((10 * density).toInt(), (2 * density).toInt(),
                (10 * density).toInt(), (2 * density).toInt())
        }
        fun controlButton(txt: String, desc: String): TextView = TextView(this).apply {
            text = txt
            contentDescription = desc
            setTextColor(0xFF9AA7C2.toInt())
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 15f)
            setPadding((18 * density).toInt(), (4 * density).toInt(),
                (18 * density).toInt(), (4 * density).toInt())
        }
        val btnBack = controlButton("◀", "Cofnij do panelu Hala")
        val btnPlus = controlButton("＋", "Powiększ okno")
        val btnMinus = controlButton("－", "Zmniejsz okno")
        val btnMin = controlButton("—", "Minimalizuj okno Hala")
        val btnClose = controlButton("✕", "Zamknij okno Hala")
        controls.addView(btnBack)
        controls.addView(btnPlus)
        controls.addView(btnMinus)
        controls.addView(btnMin)
        controls.addView(btnClose)

        val container = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            addView(controls, LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))
            addView(webView, LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))
        }

        // Wymiary okna: skala (＋/－) i minimalizacja — jedna funkcja, zero rozjazdów.
        fun applySize() {
            webView?.visibility = if (minimized) View.GONE else View.VISIBLE
            val w = if (minimized) (150 * density).toInt()
                    else (340 * density * scale).toInt().coerceAtLeast((200 * density).toInt())
            val h = if (minimized) (36 * density).toInt()
                    else (480 * density * scale).toInt().coerceAtMost((1200 * density).toInt())
            layoutParams.width = w
            layoutParams.height = h
            wm.updateViewLayout(container, layoutParams)
        }
        btnBack.setOnClickListener {
            val wv = webView ?: return@setOnClickListener
            // Artykuł otwarty w WebView → cofamy; panel jest "rootem" historii,
            // więc to zawsze wraca do głównego okna. Gdy historii brak — ładujemy panel od nowa.
            if (wv.canGoBack()) wv.goBack()
            else {
                val configured = Prefs.url(this@OverlayService)
                wv.loadUrl(if (configured.isNotEmpty()) configured
                           else "file:///android_asset/panel/panel.html")
            }
        }
        btnPlus.setOnClickListener { scale = (scale * 1.2f).coerceAtMost(2.5f); applySize() }
        btnMinus.setOnClickListener { scale = (scale / 1.2f).coerceAtLeast(0.6f); applySize() }
        btnMin.setOnClickListener { minimized = !minimized; applySize() }
        btnClose.setOnClickListener { stopSelf() }

        // Przeciąganie: TYLKO za pasek kontrolek — palenie po treści przewija
        // WebView (kiedyś listener siedział na całym kontenerze i kradł scroll).
        var downX = 0f
        var downY = 0f
        var startParamX = 0
        var startParamY = 0
        var dragging = false

        controls.setOnTouchListener { _, event ->
            when (event.actionMasked) {
                MotionEvent.ACTION_DOWN -> {
                    downX = event.rawX; downY = event.rawY
                    startParamX = layoutParams.x; startParamY = layoutParams.y
                    dragging = false
                    false
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = event.rawX - downX
                    val dy = event.rawY - downY
                    if (abs(dx) > 8 || abs(dy) > 8) dragging = true
                    if (dragging) {
                        layoutParams.x = startParamX - dx.toInt()
                        layoutParams.y = startParamY + dy.toInt()
                        wm.updateViewLayout(container, layoutParams)
                    }
                    dragging
                }
                else -> false
            }
        }

        wm.addView(container, layoutParams)
        windowContainer = container

        screenReceiver = ScreenReceiver(
            onScreenOff = { pauseWebView() },
            onScreenOn = { resumeWebView() }
        ).also {
            registerReceiver(it, ScreenReceiver.filter())
        }
    }

    private fun startForeground() {
        val channel = NotificationChannel("hal_overlay", "Hal overlay", NotificationManager.IMPORTANCE_MIN)
        getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
        val notification: Notification =
            Notification.Builder(this, "hal_overlay")
                .setContentTitle("Hal działa")
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .build()
        startForeground(1, notification)
    }

    /** Wołane z ScreenReceiver przy ACTION_SCREEN_OFF. */
    fun pauseWebView() {
        webView?.onPause()
        webView?.pauseTimers()
    }

    /** Wołane z ScreenReceiver przy ACTION_SCREEN_ON — pauza + odświeżenie treści. */
    fun resumeWebView() {
        webView?.onResume()
        webView?.resumeTimers()
        webView?.reload()
    }

    override fun onDestroy() {
        screenReceiver?.let { unregisterReceiver(it) }
        screenReceiver = null
        webView?.destroy()
        webView = null
        windowContainer?.let { try { wm.removeView(it) } catch (_: Exception) {} }
        windowContainer = null
        super.onDestroy()
    }

    private var windowContainer: View? = null
}
