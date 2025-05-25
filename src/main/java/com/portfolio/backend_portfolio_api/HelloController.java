package com.portfolio.backend_portfolio_api;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HelloController {

    @GetMapping("/hello")
    public String hello() {
        return "Hello, Spring Boot Portfolio API!";
    }

    @GetMapping("/")
    public String home() {
        return "Backend Portfolio API is running!";
    }
}
