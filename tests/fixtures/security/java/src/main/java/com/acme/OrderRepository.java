package com.acme;

import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;

public class OrderRepository {
    private final JdbcTemplate jdbcTemplate;

    public OrderRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<Map<String, Object>> search(String where, int page) {
        String sql = "SELECT * FROM orders WHERE " + where + " LIMIT 20 OFFSET " + (page * 20);
        return jdbcTemplate.queryForList(sql);
    }
}
