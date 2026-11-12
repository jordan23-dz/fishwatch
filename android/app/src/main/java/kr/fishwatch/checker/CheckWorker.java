package kr.fishwatch.checker;

import android.content.Context;

import androidx.annotation.NonNull;
import androidx.javascriptengine.JavaScriptIsolate;
import androidx.javascriptengine.JavaScriptSandbox;
import androidx.work.Worker;
import androidx.work.WorkerParameters;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;

/**
 * 점검 한 번: 검색 계획 → 네이버 검색 → 판독 → 저장 → 알림.
 * 판독 로직은 assets/engine.js 를 격리된 JavaScript 엔진에서 실행한다(화면의 직접 판독과 같은 코드).
 */
public class CheckWorker extends Worker {
    static final String KEY_MOCK = "mock";
    static final String KEY_SCHEDULED = "scheduled";
    private static final String[] MOCK_KINDS = {"cafearticle", "blog", "webkr"};

    public CheckWorker(@NonNull Context context, @NonNull WorkerParameters params) {
        super(context, params);
    }

    @NonNull
    @Override
    public Result doWork() {
        final boolean mock = getInputData().getBoolean(KEY_MOCK, false);
        final boolean scheduled = getInputData().getBoolean(KEY_SCHEDULED, false);
        if (!State.begin()) return Result.success();

        Context ctx = getApplicationContext();
        Store store = Store.get(ctx);
        String started = now();
        int calls = 0;
        int ok = 0, failed = 0, received = 0;
        String firstError = null;
        JavaScriptSandbox sandbox = null;
        JavaScriptIsolate iso = null;
        try {
            JSONObject cfg = store.getConfig();
            JSONObject naver = cfg.getJSONObject("naver");
            String id = naver.optString("client_id", "").trim();
            String secret = naver.optString("client_secret", "").trim();
            if (!mock && (id.isEmpty() || secret.isEmpty())) {
                throw new UserError("네이버 API 키가 없습니다. 설정 탭에서 Client ID와 Client Secret을 입력하세요.");
            }
            State.log(scheduled ? "예약된 자동 점검을 시작합니다." : (mock ? "예시 데이터로 시험 점검합니다." : "점검을 시작합니다."));

            try {
                sandbox = JavaScriptSandbox.createConnectedInstanceAsync(ctx).get(30, TimeUnit.SECONDS);
            } catch (Exception e) {
                throw new UserError("판독 엔진을 시작하지 못했습니다(" + describe(e) + "). Play 스토어에서 'Android System WebView'를 최신으로 업데이트한 뒤 다시 시도하세요.");
            }
            iso = sandbox.createIsolate();
            eval(iso, readAsset(ctx, "engine.js") + "\n;'ok'");

            String today = new SimpleDateFormat("yyyy-MM-dd", Locale.KOREA).format(new Date());
            String region = cfg.getJSONObject("collect").optString("region", "");

            JSONObject siteCfg = new JSONObject().put("collect", cfg.getJSONObject("collect"));
            eval(iso, "FW_PIPE.configure(" + siteCfg + ")");
            if (mock) {
                for (String kind : MOCK_KINDS) {
                    String body = readAsset(ctx, "sample/" + kind + ".json");
                    eval(iso, "FW_PIPE.ingest(" + q(kind) + "," + q("예시 데이터") + "," + q(body) + ")");
                    calls++;
                }
            } else {
                JSONObject planCfg = new JSONObject().put("collect", cfg.getJSONObject("collect"));
                JSONArray plan = new JSONArray(eval(iso,
                        "JSON.stringify(FW_PIPE.plan(" + q(today) + "," + planCfg + "))"));
                State.log("기준일 " + today + " · 검색 " + plan.length() + "건");
                NaverClient api = new NaverClient(id, secret, naver.optString("provider", "hub"));
                for (int i = 0; i < plan.length(); i++) {
                    if (isStopped()) {
                        State.log("점검이 중단되었습니다.");
                        break;
                    }
                    JSONObject p = plan.getJSONObject(i);
                    String kind = p.getString("kind");
                    String query = p.getString("query");
                    try {
                        String body = api.search(kind, query, p.optString("sort", ""));
                        ok++;
                        received += countItems(body);
                        eval(iso, "FW_PIPE.ingest(" + q(kind) + "," + q(query) + "," + q(body) + ")");
                    } catch (IOException e) {
                        failed++;
                        if (firstError == null) firstError = describe(e);
                        State.log("! " + query + " 검색 실패: " + e.getMessage());
                    }
                    calls = api.calls;
                    if ((i + 1) % 20 == 0) {
                        State.log("검색 " + (i + 1) + "/" + plan.length() + " 완료, 후보 " + eval(iso, "FW_PIPE.count()") + "건");
                    }
                }
            }

            if (!mock && ok == 0 && failed > 0) {
                throw new UserError("검색 " + failed + "건이 모두 실패해 결과가 없습니다. 인터넷 연결과 API 키를 확인하세요. 첫 오류: " + firstError);
            }
            if (!mock) {
                State.log("검색 성공 " + ok + "건" + (failed > 0 ? " · 실패 " + failed + "건" : "") + " · 검색 결과 " + received + "개");
            }
            int candidates = Integer.parseInt(eval(iso, "String(FW_PIPE.count())"));
            JSONArray rows = new JSONArray(eval(iso, "JSON.stringify(FW_PIPE.finish(" + q(today) + "," + q(region) + "))"));
            String ex = eval(iso, "FW_PIPE.excludedSummary()");
            State.log("점검 대상 " + candidates + "건 (API 호출 " + calls + "회)" + (ex.isEmpty() ? "" : " · 제외: " + ex));
            JSONObject s = store.saveRun(rows, started, now(), mock, scheduled, calls, candidates);
            State.log("위반 의심 " + s.getInt("danger") + "건 · 확인 필요 " + s.getInt("warn") + "건 · 신규 " + s.getInt("new") + "건");

            boolean notifyOn = cfg.getJSONObject("app").optBoolean("notify", true);
            if (!mock && notifyOn && s.getInt("newAlert") > 0) Notifier.newPosts(ctx, s);
            return Result.success();
        } catch (UserError e) {
            State.fail(e.getMessage());
            store.saveFailedRun(started, now(), mock, scheduled, calls, e.getMessage());
            return Result.success();
        } catch (NaverClient.AuthException e) {
            State.fail(e.getMessage());
            store.saveFailedRun(started, now(), mock, scheduled, calls, e.getMessage());
            if (scheduled) Notifier.failure(ctx, e.getMessage());
            return Result.success();
        } catch (Exception e) {
            String msg = "점검 중 오류가 났습니다: " + describe(e);
            State.fail(msg);
            store.saveFailedRun(started, now(), mock, scheduled, calls, msg);
            return Result.success();
        } finally {
            if (iso != null) iso.close();
            if (sandbox != null) sandbox.close();
            State.end();
        }
    }

    private static String eval(JavaScriptIsolate iso, String code) throws Exception {
        try {
            return iso.evaluateJavaScriptAsync(code).get(60, TimeUnit.SECONDS);
        } catch (ExecutionException e) {
            throw e.getCause() instanceof Exception ? (Exception) e.getCause() : e;
        }
    }

    private static int countItems(String body) {
        try {
            JSONArray a = new JSONObject(body).optJSONArray("items");
            return a == null ? 0 : a.length();
        } catch (Exception e) {
            return 0;
        }
    }

    /** 자바 문자열을 JavaScript 문자열 리터럴로 (JSON 문자열은 그대로 유효한 JS 리터럴) */
    private static String q(String s) {
        return JSONObject.quote(s);
    }

    static String readAsset(Context ctx, String name) throws IOException {
        try (InputStream in = ctx.getAssets().open(name)) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buf = new byte[16384];
            int n;
            while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
            return new String(out.toByteArray(), StandardCharsets.UTF_8);
        }
    }

    private static String now() {
        return new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.KOREA).format(new Date());
    }

    private static String describe(Throwable e) {
        String m = e.getMessage();
        return e.getClass().getSimpleName() + (m == null ? "" : " — " + m);
    }

    /** 사용자에게 그대로 보여 줄 오류 */
    static final class UserError extends Exception {
        UserError(String m) { super(m); }
    }
}
