package kr.fishwatch.checker;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;

import org.json.JSONArray;
import org.json.JSONObject;

/** 자동 점검 결과 알림 */
final class Notifier {
    private static final String CHANNEL = "alerts";

    private Notifier() {}

    static void newPosts(Context ctx, JSONObject s) {
        int n = s.optInt("newAlert");
        StringBuilder body = new StringBuilder();
        JSONArray titles = s.optJSONArray("newTitles");
        if (titles != null) {
            for (int i = 0; i < titles.length(); i++) {
                if (body.length() > 0) body.append('\n');
                body.append("· ").append(titles.optString(i));
            }
        }
        show(ctx, 1, "새 의심 판매글 " + n + "건", body.toString());
    }

    static void failure(Context ctx, String msg) {
        show(ctx, 2, "자동 점검 실패", msg);
    }

    private static void show(Context ctx, int id, String title, String text) {
        if (Build.VERSION.SDK_INT >= 33
                && ctx.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            return;
        }
        NotificationManager nm = ctx.getSystemService(NotificationManager.class);
        if (nm == null) return;
        NotificationChannel ch = new NotificationChannel(CHANNEL, ctx.getString(R.string.channel_alerts),
                NotificationManager.IMPORTANCE_DEFAULT);
        ch.setDescription(ctx.getString(R.string.channel_alerts_desc));
        nm.createNotificationChannel(ch);

        Intent open = new Intent(ctx, MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent pi = PendingIntent.getActivity(ctx, 0, open, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        Notification note = new Notification.Builder(ctx, CHANNEL)
                .setSmallIcon(R.drawable.ic_stat_fish)
                .setContentTitle(title)
                .setContentText(text)
                .setStyle(new Notification.BigTextStyle().bigText(text))
                .setContentIntent(pi)
                .setAutoCancel(true)
                .build();
        nm.notify(id, note);
    }
}
