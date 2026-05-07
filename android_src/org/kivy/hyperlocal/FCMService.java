package org.kivy.hyperlocal;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import android.util.Log;
import androidx.core.app.NotificationCompat;
import com.google.firebase.messaging.FirebaseMessagingService;
import com.google.firebase.messaging.RemoteMessage;

public class FCMService extends FirebaseMessagingService {

    private static final String TAG = "FCMService";
    private static final String CHANNEL_ID = "hyperlocal_channel";
    private static final String PREFS_NAME = "hyperlocal_fcm";
    private static final String KEY_PENDING_TOKEN = "pending_token";
    private static final int NOTIF_ID = 1001;

    @Override
    public void onNewToken(String token) {
        Log.d(TAG, "FCM token refreshed");
        // Store so Python picks it up on next foreground/launch and re-registers
        getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
            .edit()
            .putString(KEY_PENDING_TOKEN, token)
            .apply();
    }

    @Override
    public void onMessageReceived(RemoteMessage message) {
        String title = "Hyperlocal";
        String body  = "";

        if (message.getNotification() != null) {
            RemoteMessage.Notification n = message.getNotification();
            if (n.getTitle() != null) title = n.getTitle();
            if (n.getBody()  != null) body  = n.getBody();
        } else if (!message.getData().isEmpty()) {
            // data-only message
            title = message.getData().getOrDefault("title", "Hyperlocal");
            body  = message.getData().getOrDefault("body", "");
        } else {
            return;
        }

        // Signal the Python layer to refresh task data
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        int counter = prefs.getInt("refresh_counter", 0);
        prefs.edit().putInt("refresh_counter", counter + 1).apply();

        showNotification(title, body);
    }

    private void showNotification(String title, String body) {
        NotificationManager nm =
            (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel ch = new NotificationChannel(
                CHANNEL_ID, "Hyperlocal", NotificationManager.IMPORTANCE_HIGH);
            nm.createNotificationChannel(ch);
        }

        Intent intent = getPackageManager()
            .getLaunchIntentForPackage(getPackageName());
        if (intent != null) intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);

        int flags = Build.VERSION.SDK_INT >= Build.VERSION_CODES.S
            ? PendingIntent.FLAG_IMMUTABLE : PendingIntent.FLAG_UPDATE_CURRENT;
        PendingIntent pi = PendingIntent.getActivity(this, 0, intent, flags);

        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title)
            .setContentText(body)
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setContentIntent(pi);

        nm.notify(NOTIF_ID, builder.build());
    }
}
