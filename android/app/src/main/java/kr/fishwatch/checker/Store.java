package kr.fishwatch.checker;

import android.content.ContentValues;
import android.content.Context;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

/** 설정(SharedPreferences)과 판매글·점검 기록(SQLite). 모든 데이터는 기기 안에만 저장된다. */
final class Store extends SQLiteOpenHelper {
    private static Store instance;
    private final SharedPreferences prefs;

    static synchronized Store get(Context ctx) {
        if (instance == null) instance = new Store(ctx.getApplicationContext());
        return instance;
    }

    private Store(Context ctx) {
        super(ctx, "fishwatch.db", null, 2);
        prefs = ctx.getSharedPreferences("fishwatch", Context.MODE_PRIVATE);
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE posts(link TEXT PRIMARY KEY, site TEXT, source TEXT, query TEXT, title TEXT, description TEXT,"
                + " post_date TEXT, first_seen TEXT, last_seen TEXT, sev TEXT, findings TEXT, extra TEXT, review TEXT DEFAULT '', demo INTEGER DEFAULT 0)");
        db.execSQL("CREATE TABLE runs(id INTEGER PRIMARY KEY AUTOINCREMENT, started TEXT, finished TEXT, mock INTEGER,"
                + " scheduled INTEGER, calls INTEGER, candidates INTEGER, danger INTEGER, warn INTEGER, new INTEGER, error TEXT)");
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldV, int newV) {
        if (oldV < 2) db.execSQL("ALTER TABLE posts ADD COLUMN demo INTEGER DEFAULT 0");
    }

    /* ---------- 설정 ---------- */

    static JSONObject defaults() {
        try {
            return new JSONObject("{"
                    + "\"naver\":{\"provider\":\"hub\",\"client_id\":\"\",\"client_secret\":\"\"},"
                    + "\"collect\":{\"sources\":[\"cafearticle\",\"blog\",\"webkr\"],\"max_calls\":800,\"region\":\"\","
                    + "\"extra_queries\":[\"자연산 광어 판매\",\"자연산 우럭 판매\",\"자연산 전복 판매\",\"대문어 판매\"],"
                    + "\"exclude\":[\"nonfood\",\"processed\",\"imported\",\"farmed\"],\"title_species\":true},"
                    + "\"report\":{\"min_severity\":\"warn\"},"
                    + "\"app\":{\"auto_run\":false,\"run_time\":\"08:47\",\"notify\":true}}");
        } catch (JSONException e) {
            throw new IllegalStateException(e);
        }
    }

    synchronized JSONObject getConfig() {
        JSONObject cfg = defaults();
        String saved = prefs.getString("config", null);
        if (saved != null) {
            try {
                merge(cfg, new JSONObject(saved));
            } catch (JSONException ignored) { }
        }
        return cfg;
    }

    /** 화면에서 받은 설정을 저장한다. Secret 칸이 비어 있으면 기존 값을 유지한다. */
    synchronized JSONObject saveConfig(JSONObject incoming) throws JSONException {
        JSONObject cfg = getConfig();
        String oldSecret = cfg.getJSONObject("naver").optString("client_secret", "");
        merge(cfg, incoming);
        JSONObject n = cfg.getJSONObject("naver");
        n.remove("has_secret");
        if (n.optString("client_secret", "").trim().isEmpty()) n.put("client_secret", oldSecret);
        prefs.edit().putString("config", cfg.toString()).apply();
        return cfg;
    }

    static JSONObject masked(JSONObject cfg) throws JSONException {
        JSONObject c = new JSONObject(cfg.toString());
        JSONObject n = c.getJSONObject("naver");
        n.put("has_secret", !n.optString("client_secret", "").isEmpty());
        n.put("client_secret", "");
        return c;
    }

    private static void merge(JSONObject base, JSONObject add) throws JSONException {
        Iterator<String> it = add.keys();
        while (it.hasNext()) {
            String sec = it.next();
            Object v = add.get(sec);
            if (v instanceof JSONObject && base.optJSONObject(sec) != null) {
                JSONObject b = base.getJSONObject(sec);
                JSONObject a = (JSONObject) v;
                Iterator<String> k = a.keys();
                while (k.hasNext()) {
                    String key = k.next();
                    b.put(key, a.get(key));
                }
            }
        }
    }

    /* ---------- 판매글 ---------- */

    /** 점검 결과를 저장하고 요약을 돌려준다. */
    synchronized JSONObject saveRun(JSONArray rows, String started, String finished, boolean mock, boolean scheduled,
                                    int calls, int candidates) throws JSONException {
        SQLiteDatabase db = getWritableDatabase();
        int danger = 0, warn = 0, fresh = 0, freshAlert = 0;
        List<String> freshTitles = new ArrayList<>();
        db.beginTransaction();
        try {
            // 예시 데이터 결과는 다음 점검 때 지운다 (실제 결과와 섞이지 않게)
            db.delete("posts", "demo=1", null);
            for (int i = 0; i < rows.length(); i++) {
                JSONObject r = rows.getJSONObject(i);
                String link = r.getString("link");
                String sev = r.getString("sev");
                if ("danger".equals(sev)) danger++;
                if ("warn".equals(sev)) warn++;
                String first = started;
                boolean isNew = true;
                try (Cursor c = db.rawQuery("SELECT first_seen FROM posts WHERE link=?", new String[]{link})) {
                    if (c.moveToFirst()) {
                        first = c.getString(0);
                        isNew = false;
                    }
                }
                ContentValues v = new ContentValues();
                v.put("site", r.optString("site"));
                v.put("source", r.optString("source"));
                v.put("query", r.optString("query"));
                v.put("title", r.optString("title"));
                v.put("description", r.optString("description"));
                v.put("post_date", r.isNull("post_date") ? null : r.optString("post_date"));
                v.put("last_seen", started);
                v.put("sev", sev);
                v.put("findings", r.getJSONArray("findings").toString());
                v.put("extra", r.optJSONObject("extra") == null ? "{}" : r.getJSONObject("extra").toString());
                if (isNew) {
                    v.put("link", link);
                    v.put("first_seen", first);
                    v.put("review", "");
                    v.put("demo", mock ? 1 : 0);
                    db.insert("posts", null, v);
                    fresh++;
                    if ("danger".equals(sev) || "warn".equals(sev)) {
                        freshAlert++;
                        if (freshTitles.size() < 3) freshTitles.add(r.optString("title"));
                    }
                } else {
                    db.update("posts", v, "link=?", new String[]{link});
                }
            }
            ContentValues run = new ContentValues();
            run.put("started", started);
            run.put("finished", finished);
            run.put("mock", mock ? 1 : 0);
            run.put("scheduled", scheduled ? 1 : 0);
            run.put("calls", calls);
            run.put("candidates", candidates);
            run.put("danger", danger);
            run.put("warn", warn);
            run.put("new", fresh);
            db.insert("runs", null, run);
            db.setTransactionSuccessful();
        } finally {
            db.endTransaction();
        }
        JSONObject s = new JSONObject();
        s.put("danger", danger).put("warn", warn).put("new", fresh).put("newAlert", freshAlert)
                .put("newTitles", new JSONArray(freshTitles)).put("candidates", candidates).put("calls", calls);
        return s;
    }

    synchronized void saveFailedRun(String started, String finished, boolean mock, boolean scheduled, int calls, String error) {
        ContentValues run = new ContentValues();
        run.put("started", started);
        run.put("finished", finished);
        run.put("mock", mock ? 1 : 0);
        run.put("scheduled", scheduled ? 1 : 0);
        run.put("calls", calls);
        run.put("candidates", 0);
        run.put("danger", 0);
        run.put("warn", 0);
        run.put("new", 0);
        run.put("error", error);
        getWritableDatabase().insert("runs", null, run);
    }

    synchronized JSONArray runs(int limit) throws JSONException {
        JSONArray out = new JSONArray();
        try (Cursor c = getReadableDatabase().rawQuery("SELECT * FROM runs ORDER BY id DESC LIMIT " + limit, null)) {
            while (c.moveToNext()) out.put(rowToJson(c));
        }
        return out;
    }

    synchronized int openCount() {
        try (Cursor c = getReadableDatabase().rawQuery(
                "SELECT COUNT(*) FROM posts WHERE sev IN ('danger','warn') AND COALESCE(review,'')=''", null)) {
            return c.moveToFirst() ? c.getInt(0) : 0;
        }
    }

    synchronized JSONObject posts(String sev, String site, String review, int offset, int limit) throws JSONException {
        StringBuilder sql = new StringBuilder("SELECT * FROM posts WHERE 1=1");
        List<String> args = new ArrayList<>();
        if (sev != null && !sev.isEmpty()) {
            sql.append(" AND sev=?");
            args.add(sev);
        } else {
            sql.append(" AND sev IN ('danger','warn')");
        }
        if (site != null && !site.isEmpty()) {
            sql.append(" AND site=?");
            args.add(site);
        }
        if ("open".equals(review)) {
            sql.append(" AND COALESCE(review,'')=''");
        } else if (review != null && !review.isEmpty()) {
            sql.append(" AND review=?");
            args.add(review);
        }
        SQLiteDatabase db = getReadableDatabase();
        long total;
        try (Cursor c = db.rawQuery(sql.toString().replaceFirst("SELECT \\*", "SELECT COUNT(*)"), args.toArray(new String[0]))) {
            total = c.moveToFirst() ? c.getLong(0) : 0;
        }
        int lim = Math.max(1, Math.min(limit, 5000));
        int off = Math.max(0, offset);
        sql.append(" ORDER BY CASE sev WHEN 'danger' THEN 0 WHEN 'warn' THEN 1 ELSE 2 END, first_seen DESC, link LIMIT ")
                .append(lim).append(" OFFSET ").append(off);
        JSONArray posts = new JSONArray();
        try (Cursor c = db.rawQuery(sql.toString(), args.toArray(new String[0]))) {
            while (c.moveToNext()) {
                JSONObject o = rowToJson(c);
                o.put("findings", new JSONArray(o.optString("findings", "[]")));
                o.put("extra", new JSONObject(o.optString("extra", "{}")));
                posts.put(o);
            }
        }
        JSONArray sites = new JSONArray();
        try (Cursor c = db.rawQuery("SELECT DISTINCT site FROM posts ORDER BY site", null)) {
            while (c.moveToNext()) sites.put(c.getString(0));
        }
        return new JSONObject().put("posts", posts).put("sites", sites).put("total", total);
    }

    synchronized void setReview(String link, String review) {
        ContentValues v = new ContentValues();
        v.put("review", review == null ? "" : review);
        getWritableDatabase().update("posts", v, "link=?", new String[]{link});
    }

    synchronized void clearAll() {
        SQLiteDatabase db = getWritableDatabase();
        db.delete("posts", null, null);
        db.delete("runs", null, null);
    }

    private static JSONObject rowToJson(Cursor c) throws JSONException {
        JSONObject o = new JSONObject();
        for (int i = 0; i < c.getColumnCount(); i++) {
            String name = c.getColumnName(i);
            switch (c.getType(i)) {
                case Cursor.FIELD_TYPE_INTEGER:
                    o.put(name, c.getLong(i));
                    break;
                case Cursor.FIELD_TYPE_NULL:
                    o.put(name, JSONObject.NULL);
                    break;
                default:
                    o.put(name, c.getString(i));
            }
        }
        return o;
    }
}
