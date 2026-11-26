package com.acme;

import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;

public class OrderService {
    private final JdbcTemplate jdbcTemplate;
    private final OrderRepository repository;

    public OrderService(JdbcTemplate jdbcTemplate, OrderRepository repository) {
        this.jdbcTemplate = jdbcTemplate;
        this.repository = repository;
    }

    public List<Map<String, Object>> findByCustomer(String customer, int page) {
        return repository.search("customer = '" + customer + "'", page);
    }

    public List<Map<String, Object>> findByCustomerSafe(String customer) {
        return jdbcTemplate.queryForList("SELECT * FROM orders WHERE customer = ?", customer);
    }

    public Map<String, Object> findById(Long id) {
        return jdbcTemplate.queryForMap("SELECT * FROM orders WHERE id = " + id);
    }
}
