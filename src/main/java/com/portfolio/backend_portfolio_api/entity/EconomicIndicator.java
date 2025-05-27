package com.portfolio.backend_portfolio_api.entity;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Column;
import java.time.LocalDateTime; // LocalDateTime をインポート

@Entity
@Table(name = "economic_indicator") // テーブル名を指定
public class EconomicIndicator {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id; // PK は Long 型に変更

    @Column(name = "date", nullable = false)
    private LocalDateTime date;

    @Column(name = "country", nullable = false)
    private String country;

    @Column(name = "indicator", nullable = false)
    private String indicator;

    @Column(name = "actual", nullable = false)
    private Double actual;

    @Column(name = "forecast", nullable = false)
    private Double forecast;

    @Column(name = "previous", nullable = false)
    private Double previous;

    @Column(name = "impact", nullable = false, length = 10) // HIGH, MEDIUM, LOW などが入るため長さを指定
    private String impact;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    // 空のコンストラクタ
    public EconomicIndicator() {}

    // 全フィールドを持つコンストラクタ（必要であれば）
    public EconomicIndicator(LocalDateTime date, String country, String indicator, Double actual, Double forecast, Double previous, String impact, LocalDateTime createdAt, LocalDateTime updatedAt) {
        this.date = date;
        this.country = country;
        this.indicator = indicator;
        this.actual = actual;
        this.forecast = forecast;
        this.previous = previous;
        this.impact = impact;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    // Getter、Setter
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public LocalDateTime getDate() {
        return date;
    }

    public void setDate(LocalDateTime date) {
        this.date = date;
    }

    public String getCountry() {
        return country;
    }

    public void setCountry(String country) {
        this.country = country;
    }

    public String getIndicator() {
        return indicator;
    }

    public void setIndicator(String indicator) {
        this.indicator = indicator;
    }

    public Double getActual() {
        return actual;
    }

    public void setActual(Double actual) {
        this.actual = actual;
    }

    public Double getForecast() {
        return forecast;
    }

    public void setForecast(Double forecast) {
        this.forecast = forecast;
    }

    public Double getPrevious() {
        return previous;
    }

    public void setPrevious(Double previous) {
        this.previous = previous;
    }

    public String getImpact() {
        return impact;
    }

    public void setImpact(String impact) {
        this.impact = impact;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }
}