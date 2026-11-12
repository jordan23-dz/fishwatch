package kr.fishwatch.checker;

import android.content.Context;

import androidx.work.Constraints;
import androidx.work.Data;
import androidx.work.ExistingPeriodicWorkPolicy;
import androidx.work.ExistingWorkPolicy;
import androidx.work.NetworkType;
import androidx.work.OneTimeWorkRequest;
import androidx.work.PeriodicWorkRequest;
import androidx.work.WorkManager;

import org.json.JSONObject;

import java.util.Calendar;
import java.util.concurrent.TimeUnit;

/** 지금 점검(1회)과 매일 자동 점검(주기 작업)을 WorkManager에 등록한다. */
final class Scheduler {
    static final String NOW = "fw-now";
    static final String DAILY = "fw-daily";

    private Scheduler() {}

    static void runNow(Context ctx, boolean mock) {
        OneTimeWorkRequest req = new OneTimeWorkRequest.Builder(CheckWorker.class)
                .setInputData(new Data.Builder().putBoolean(CheckWorker.KEY_MOCK, mock).build())
                .build();
        WorkManager.getInstance(ctx).enqueueUniqueWork(NOW, ExistingWorkPolicy.KEEP, req);
    }

    /** 설정에 맞춰 매일 점검을 켜거나 끈다. 시각은 대략적이며 기기 절전 상태에 따라 늦어질 수 있다. */
    static void apply(Context ctx, JSONObject cfg) {
        JSONObject app = cfg.optJSONObject("app");
        WorkManager wm = WorkManager.getInstance(ctx);
        if (app == null || !app.optBoolean("auto_run", false)) {
            wm.cancelUniqueWork(DAILY);
            return;
        }
        long delay = millisUntil(app.optString("run_time", "08:47"));
        PeriodicWorkRequest req = new PeriodicWorkRequest.Builder(CheckWorker.class, 24, TimeUnit.HOURS)
                .setInitialDelay(delay, TimeUnit.MILLISECONDS)
                .setConstraints(new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
                .setInputData(new Data.Builder().putBoolean(CheckWorker.KEY_SCHEDULED, true).build())
                .build();
        wm.enqueueUniquePeriodicWork(DAILY, ExistingPeriodicWorkPolicy.CANCEL_AND_REENQUEUE, req);
    }

    static long millisUntil(String hhmm) {
        int h = 8, m = 47;
        try {
            String[] p = hhmm.split(":");
            h = Integer.parseInt(p[0]);
            m = Integer.parseInt(p[1]);
        } catch (RuntimeException ignored) { }
        Calendar now = Calendar.getInstance();
        Calendar next = (Calendar) now.clone();
        next.set(Calendar.HOUR_OF_DAY, h);
        next.set(Calendar.MINUTE, m);
        next.set(Calendar.SECOND, 0);
        next.set(Calendar.MILLISECOND, 0);
        if (!next.after(now)) next.add(Calendar.DAY_OF_MONTH, 1);
        return next.getTimeInMillis() - now.getTimeInMillis();
    }
}
