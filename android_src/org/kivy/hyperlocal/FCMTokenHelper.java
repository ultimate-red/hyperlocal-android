package org.kivy.hyperlocal;

import android.content.Context;
import android.util.Log;
import com.google.android.gms.tasks.OnCompleteListener;
import com.google.android.gms.tasks.Task;
import com.google.firebase.FirebaseApp;
import com.google.firebase.FirebaseOptions;
import com.google.firebase.messaging.FirebaseMessaging;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class FCMTokenHelper {
    private static final String TAG = "FCMTokenHelper";

    public static String getTokenSync(Context context, long timeoutSeconds) {
        // Initialize Firebase in Java — more reliable than doing it via pyjnius.
        if (FirebaseApp.getApps(context).isEmpty()) {
            Log.d(TAG, "Firebase not initialized, initializing now");
            try {
                FirebaseOptions options = new FirebaseOptions.Builder()
                    .setApplicationId("1:252773985780:android:ffec27008c677272a69da1")
                    .setProjectId("hyperlocal-platform-app")
                    .setApiKey("AIzaSyCL2nV-soHYJlWsI2rMNXsoYqqCeWCso_0")
                    .setGcmSenderId("252773985780")
                    .build();
                FirebaseApp.initializeApp(context, options);
                Log.d(TAG, "Firebase initialized successfully");
            } catch (Exception e) {
                Log.e(TAG, "Firebase init failed: " + e.getMessage());
                return null;
            }
        } else {
            Log.d(TAG, "Firebase already initialized");
        }

        final CountDownLatch latch = new CountDownLatch(1);
        final String[] result = {null};

        FirebaseMessaging.getInstance().getToken()
            .addOnCompleteListener(Executors.newSingleThreadExecutor(), new OnCompleteListener<String>() {
                @Override
                public void onComplete(Task<String> task) {
                    if (task.isSuccessful()) {
                        result[0] = task.getResult();
                        Log.d(TAG, "Token fetched successfully");
                    } else {
                        Exception e = task.getException();
                        Log.e(TAG, "Token fetch failed: " + (e != null ? e.getMessage() : "unknown"));
                    }
                    latch.countDown();
                }
            });

        try {
            if (!latch.await(timeoutSeconds, TimeUnit.SECONDS)) {
                Log.w(TAG, "Token fetch timed out after " + timeoutSeconds + "s");
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            Log.e(TAG, "Token fetch interrupted");
        }

        return result[0];
    }
}
