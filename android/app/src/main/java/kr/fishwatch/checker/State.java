package kr.fishwatch.checker;

import org.json.JSONArray;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

/** 진행 중인 점검의 상태와 로그. 화면이 1초 간격으로 읽어 간다. */
final class State {
    private static boolean running = false;
    private static String error = null;
    private static final List<String> LOG = new ArrayList<>();

    private State() {}

    static synchronized boolean begin() {
        if (running) return false;
        running = true;
        error = null;
        LOG.clear();
        return true;
    }

    static synchronized void end() { running = false; }

    static synchronized boolean isRunning() { return running; }

    static synchronized void fail(String msg) {
        error = msg;
        log("오류: " + msg);
    }

    static synchronized String error() { return error; }

    static synchronized void log(String msg) {
        String t = new SimpleDateFormat("HH:mm:ss", Locale.KOREA).format(new Date());
        LOG.add(t + "  " + msg);
        while (LOG.size() > 200) LOG.remove(0);
    }

    static synchronized JSONArray logJson() { return new JSONArray(LOG); }
}
