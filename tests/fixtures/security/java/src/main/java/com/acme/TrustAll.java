package com.acme;

import java.security.cert.X509Certificate;
import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.X509TrustManager;

public class TrustAll implements X509TrustManager {
    public void checkClientTrusted(X509Certificate[] chain, String authType) { // expect: SEC-TLS
    }

    public void checkServerTrusted(X509Certificate[] chain, String authType) { // expect: SEC-TLS
    }

    public X509Certificate[] getAcceptedIssuers() {
        return new X509Certificate[0];
    }

    public static void install() {
        HttpsURLConnection.setDefaultHostnameVerifier((host, session) -> true); // expect: SEC-TLS
    }
}
