package com.acme;

import java.math.BigDecimal;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.text.SimpleDateFormat;
import java.time.format.DateTimeFormatter;
import java.util.Random;
import javax.crypto.Cipher;
import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilderFactory;
import org.springframework.transaction.annotation.Transactional;

// Corpus: comprobaciones estructurales en Java.
public class Patterns {
    private static final SimpleDateFormat FORMAT = new SimpleDateFormat("yyyy-MM-dd"); // expect: BUG-SHARED-DATEFORMAT
    private static final DateTimeFormatter SAFE_FORMAT = DateTimeFormatter.ISO_DATE;
    private String adminPassword = "Adm1n-P@ssw0rd"; // expect: SEC-SECRET
    private String passwordParam = "password";
    private final Random jitter = new Random();

    public boolean isActive(String status) {
        if (status == null) {
            return false;
        }
        return status == "ACTIVE"; // expect: BUG-STRING-EQ
    }

    public boolean isActiveOk(String status) {
        return "ACTIVE".equals(status);
    }

    public BigDecimal price() {
        BigDecimal good = BigDecimal.valueOf(0.1);
        return good.add(new BigDecimal(0.1)); // expect: BUG-BIGDECIMAL-DOUBLE
    }

    public void sleepy() {
        try {
            Thread.sleep(100);
        } catch (InterruptedException e) { // expect: BUG-INTERRUPTED
            System.out.println("interrupted");
        }
        try {
            Thread.sleep(100);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    public void quiet() {
        try {
            risky();
        } catch (Exception e) { // expect: BUG-EMPTY-CATCH
        }
    }

    @Transactional
    private void saveInternal() { // expect: BUG-TX-PRIVATE
    }

    @Transactional
    public void save() {
        saveInternal();
    }

    public byte[] hashPassword(String password) throws Exception {
        MessageDigest md = MessageDigest.getInstance("MD5"); // expect: SEC-WEAKHASH
        MessageDigest ok = MessageDigest.getInstance("SHA-256");
        ok.update(password.getBytes());
        return md.digest(password.getBytes());
    }

    public void ciphers() throws Exception {
        Cipher.getInstance("AES/ECB/PKCS5Padding"); // expect: SEC-WEAKCIPHER
        Cipher.getInstance("AES/GCM/NoPadding");
    }

    public String sessionToken() {
        String sessionToken = Long.toHexString(new Random().nextLong()); // expect: SEC-WEAKRANDOM
        String nonce = Long.toHexString(new SecureRandom().nextLong());
        return sessionToken + nonce + jitter.nextInt();
    }

    private void risky() {
    }
}
