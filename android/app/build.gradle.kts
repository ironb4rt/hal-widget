plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "pl.hal.widget"
    compileSdk = 35

    defaultConfig {
        applicationId = "pl.hal.widget"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
    }
}

dependencies {
    // Celowo zero zewnętrznych zależności — mniejszy APK, mniej powierzchni na problemy.
    implementation("androidx.lifecycle:lifecycle-service:2.8.7")
}
