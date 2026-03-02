# Flutter wrapper
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.** { *; }
-keep class io.flutter.util.** { *; }
-keep class io.flutter.view.** { *; }
-keep class io.flutter.** { *; }
-keep class io.flutter.plugins.** { *; }

# Firebase
-keep class com.google.firebase.** { *; }

# Google Sign-In / Play Services
-keep class com.google.android.gms.** { *; }
-keep class com.google.android.gms.auth.** { *; }
-keep class com.google.android.gms.common.** { *; }

# Keep just_audio classes
-keep class com.google.android.exoplayer2.** { *; }

# Play Core (Flutter deferred components 참조 — Play Store 미사용이므로 경고 무시)
-dontwarn com.google.android.play.core.**
