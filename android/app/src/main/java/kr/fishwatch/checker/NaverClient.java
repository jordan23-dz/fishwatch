package kr.fishwatch.checker;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

/** 네이버 검색 API 호출 (NAVER API HUB 또는 기존 개발자센터 키). */
final class NaverClient {
    static final String HUB_BASE = "https://naverapihub.apigw.ntruss.com/search/v1/";
    static final String LEGACY_BASE = "https://openapi.naver.com/v1/search/";

    /** 키가 틀려 더 진행할 수 없는 경우 */
    static final class AuthException extends Exception {
        AuthException(String m) { super(m); }
    }

    private final String id;
    private final String secret;
    private final boolean legacy;
    int calls = 0;

    NaverClient(String id, String secret, String provider) {
        this.id = id == null ? "" : id.trim();
        this.secret = secret == null ? "" : secret.trim();
        this.legacy = "legacy".equals(provider);
    }

    String search(String kind, String query, String sort) throws IOException, AuthException {
        StringBuilder u = new StringBuilder(legacy ? LEGACY_BASE + kind + ".json" : HUB_BASE + kind);
        u.append("?query=").append(URLEncoder.encode(query, "UTF-8")).append("&display=100&start=1");
        if (sort != null && !sort.isEmpty()) u.append("&sort=").append(sort);

        IOException last = null;
        for (int attempt = 0; attempt < 3; attempt++) {
            HttpURLConnection c = (HttpURLConnection) new URL(u.toString()).openConnection();
            try {
                c.setConnectTimeout(15000);
                c.setReadTimeout(20000);
                if (legacy) {
                    c.setRequestProperty("X-Naver-Client-Id", id);
                    c.setRequestProperty("X-Naver-Client-Secret", secret);
                } else {
                    c.setRequestProperty("X-NCP-APIGW-API-KEY-ID", id);
                    c.setRequestProperty("X-NCP-APIGW-API-KEY", secret);
                }
                int code = c.getResponseCode();
                if (code == 200) {
                    calls++;
                    pause(120);
                    return read(c.getInputStream());
                }
                String body = read(c.getErrorStream());
                if (body.length() > 200) body = body.substring(0, 200);
                if (code == 401 || code == 403) {
                    throw new AuthException("네이버 API 인증 실패(" + code + "). 설정의 Client ID·Secret과 키 종류를 확인하세요. 계정 IAM 키가 아니라 API HUB 앱의 [인증 정보] 값이어야 합니다.");
                }
                if (code == 429 && attempt < 2) {
                    pause(2000L * (attempt + 1));
                    continue;
                }
                throw new IOException("HTTP " + code + " " + body);
            } catch (IOException e) {
                last = e;
                if (attempt < 2 && !(e.getMessage() != null && e.getMessage().startsWith("HTTP "))) {
                    pause(2000);
                    continue;
                }
                throw e;
            } finally {
                c.disconnect();
            }
        }
        throw last != null ? last : new IOException("요청 실패");
    }

    /** 키 확인: 카페글 검색 1건 호출. {ok, status, message, body} */
    org.json.JSONObject test() {
        org.json.JSONObject o = new org.json.JSONObject();
        try {
            String u = (legacy ? LEGACY_BASE + "cafearticle.json" : HUB_BASE + "cafearticle")
                    + "?query=" + URLEncoder.encode("전복", "UTF-8") + "&display=1";
            HttpURLConnection c = (HttpURLConnection) new URL(u).openConnection();
            try {
                c.setConnectTimeout(15000);
                c.setReadTimeout(20000);
                if (legacy) {
                    c.setRequestProperty("X-Naver-Client-Id", id);
                    c.setRequestProperty("X-Naver-Client-Secret", secret);
                } else {
                    c.setRequestProperty("X-NCP-APIGW-API-KEY-ID", id);
                    c.setRequestProperty("X-NCP-APIGW-API-KEY", secret);
                }
                int code = c.getResponseCode();
                String body = read(code == 200 ? c.getInputStream() : c.getErrorStream());
                o.put("ok", code == 200).put("status", code).put("body", body.length() > 300 ? body.substring(0, 300) : body);
                if (code == 200) {
                    o.put("message", "키가 정상입니다. 카페글 검색 '전복' 결과 " + new org.json.JSONObject(body).optLong("total") + "건.");
                } else if (code == 401) {
                    o.put("message", "실패(HTTP 401). Client ID·Secret 값이 틀렸거나, Application에 이 검색 API를 체크하지 않았습니다.");
                } else if (code == 403) {
                    o.put("message", "실패(HTTP 403). Application의 API 선택에 카페글·블로그·웹문서 검색이 있는지 확인하세요.");
                } else {
                    o.put("message", "실패(HTTP " + code + ").");
                }
            } finally {
                c.disconnect();
            }
        } catch (Exception e) {
            try {
                o.put("ok", false).put("message", "네이버 서버에 연결하지 못했습니다: " + e.getMessage()).put("body", "");
            } catch (org.json.JSONException ignored) { }
        }
        return o;
    }

    private static String read(InputStream in) throws IOException {
        if (in == null) return "";
        try (InputStream s = in) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buf = new byte[8192];
            int n;
            while ((n = s.read(buf)) > 0) out.write(buf, 0, n);
            return new String(out.toByteArray(), StandardCharsets.UTF_8);
        }
    }

    private static void pause(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException ignored) { Thread.currentThread().interrupt(); }
    }
}
