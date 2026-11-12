package kr.fishwatch.checker;

import android.Manifest;
import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.webkit.JavascriptInterface;

import org.json.JSONObject;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/** 화면(assets/index.html)에서 window.FW 로 호출하는 기능. 모든 값은 JSON 문자열로 주고받는다. */
final class Bridge {
    private final Activity activity;
    private final Store store;

    Bridge(Activity activity) {
        this.activity = activity;
        this.store = Store.get(activity);
    }

    @JavascriptInterface
    public String getState() {
        try {
            JSONObject o = new JSONObject();
            o.put("running", State.isRunning());
            o.put("log", State.logJson());
            o.put("error", State.error() == null ? JSONObject.NULL : State.error());
            o.put("runs", store.runs(10));
            o.put("open", store.openCount());
            o.put("config", Store.masked(store.getConfig()));
            o.put("today", new SimpleDateFormat("yyyy-MM-dd", Locale.KOREA).format(new Date()));
            return o.toString();
        } catch (Exception e) {
            return err(e);
        }
    }

    @JavascriptInterface
    public String getPosts(String sev, String site, String review, int offset, int limit) {
        try {
            return store.posts(sev, site, review, offset, limit).toString();
        } catch (Exception e) {
            return err(e);
        }
    }

    @JavascriptInterface
    public String setReview(String link, String review) {
        store.setReview(link, review);
        return "{\"ok\":true}";
    }

    @JavascriptInterface
    public String runNow(boolean mock) {
        if (State.isRunning()) return "{\"started\":false,\"message\":\"이미 점검이 진행 중입니다.\"}";
        Scheduler.runNow(activity, mock);
        return "{\"started\":true}";
    }

    @JavascriptInterface
    public String saveConfig(String json) {
        try {
            JSONObject cfg = store.saveConfig(new JSONObject(json));
            Scheduler.apply(activity, cfg);
            return new JSONObject().put("saved", true).put("config", Store.masked(cfg)).toString();
        } catch (Exception e) {
            return err(e);
        }
    }

    /** 키 확인 (JavaBridge 스레드에서 실행되므로 네트워크 호출 가능). Secret이 비면 저장된 값 사용 */
    @JavascriptInterface
    public String testKey(String provider, String id, String secret) {
        try {
            JSONObject n = store.getConfig().getJSONObject("naver");
            String cid = id == null || id.trim().isEmpty() ? n.optString("client_id", "") : id;
            String sec = secret == null || secret.trim().isEmpty() ? n.optString("client_secret", "") : secret;
            if (cid.trim().isEmpty() || sec.trim().isEmpty()) {
                return "{\"ok\":false,\"message\":\"Client ID와 Client Secret을 입력하세요.\"}";
            }
            return new NaverClient(cid, sec, provider).test().toString();
        } catch (Exception e) {
            return err(e);
        }
    }

    @JavascriptInterface
    public String clearData() {
        store.clearAll();
        return "{\"ok\":true}";
    }

    @JavascriptInterface
    public void openUrl(String url) {
        if (url == null || !(url.startsWith("https://") || url.startsWith("http://"))) return;
        activity.runOnUiThread(() -> {
            try {
                activity.startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
            } catch (ActivityNotFoundException ignored) { }
        });
    }

    @JavascriptInterface
    public boolean notificationsAllowed() {
        return Build.VERSION.SDK_INT < 33
                || activity.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED;
    }

    @JavascriptInterface
    public void requestNotifications() {
        if (Build.VERSION.SDK_INT >= 33 && !notificationsAllowed()) {
            activity.runOnUiThread(() ->
                    activity.requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 1));
        }
    }

    @JavascriptInterface
    public String appVersion() {
        try {
            PackageInfo p = activity.getPackageManager().getPackageInfo(activity.getPackageName(), 0);
            return p.versionName;
        } catch (PackageManager.NameNotFoundException e) {
            return "";
        }
    }

    @JavascriptInterface
    public void exitApp() {
        activity.runOnUiThread(activity::finish);
    }

    private static String err(Exception e) {
        try {
            return new JSONObject().put("error", String.valueOf(e.getMessage())).toString();
        } catch (Exception x) {
            return "{\"error\":\"unknown\"}";
        }
    }
}
