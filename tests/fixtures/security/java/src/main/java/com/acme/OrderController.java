package com.acme;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import org.apache.commons.io.FilenameUtils;
import org.springframework.expression.spel.standard.SpelExpressionParser;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.HtmlUtils;

// Corpus: Spring MVC. Cada línea con "expect:" debe producir exactamente esos hallazgos.
@RestController
@RequestMapping("/orders")
public class OrderController {
    private final OrderService service;
    private final RestTemplate restTemplate = new RestTemplate();

    public OrderController(OrderService service) {
        this.service = service;
    }

    @GetMapping("/search")
    public Object search(@RequestParam String customer, @RequestParam int page) {
        return service.findByCustomer(customer, page); // expect: SEC-SQLI
    }

    @GetMapping("/{id}")
    public Object byId(@PathVariable Long id) {
        return service.findById(id);
    }

    @GetMapping("/safe")
    public Object safe(@RequestParam String customer) {
        return service.findByCustomerSafe(customer);
    }

    @GetMapping("/export")
    public byte[] export(@RequestParam String file) throws IOException {
        byte[] ok = Files.readAllBytes(Paths.get("/exports", FilenameUtils.getName(file)));
        File target = new File("/exports/" + file); // expect: SEC-PATH
        return ok.length > 0 ? ok : Files.readAllBytes(target.toPath());
    }

    @PostMapping("/notify")
    public String notifyPartner(@RequestBody NotifyRequest body) {
        return restTemplate.getForObject(body.getCallbackUrl(), String.class); // expect: SEC-SSRF
    }

    @PostMapping("/convert")
    public String convert(@RequestParam String format) throws IOException {
        Runtime.getRuntime().exec(new String[] {"convert", "--to", format}); // expect: SEC-CMDI
        new ProcessBuilder("convert", "--version").start();
        return "ok";
    }

    @GetMapping("/eval")
    public Object eval(@RequestParam String expr) {
        return new SpelExpressionParser().parseExpression(expr).getValue(); // expect: SEC-CODEI
    }

    @GetMapping("/legacy")
    public void legacy(HttpServletRequest request, HttpServletResponse response) throws IOException {
        String next = request.getParameter("next");
        String name = request.getParameter("name");
        response.getWriter().write("<p>" + HtmlUtils.htmlEscape(name) + "</p>");
        response.getWriter().write("<p>" + name + "</p>"); // expect: SEC-XSS
        response.sendRedirect(next); // expect: SEC-REDIRECT
    }
}
