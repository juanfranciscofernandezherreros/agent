package com.acme;

import java.sql.Connection;
import java.sql.Statement;
import org.springframework.kafka.annotation.KafkaListener;

// Corpus: mensajes de Kafka como entrada externa.
public class OrderEvents {
    private Connection connection;

    @KafkaListener(topics = "orders.cancelled")
    public void onCancelled(String orderId) throws Exception {
        Statement statement = connection.createStatement();
        statement.executeUpdate("DELETE FROM orders WHERE id = '" + orderId + "'"); // expect: SEC-SQLI
    }
}
