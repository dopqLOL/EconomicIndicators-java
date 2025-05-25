package com.portfolio.backend_portfolio_api.domain.model;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Column;
import java.time.LocalDate;
import java.math.BigDecimal;

@Entity
@Table(name = "economic_indicators") // DB内のテーブル名を指定
public class EconomicIndicator {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY) // 主キー自動生成
    private Long id;

    @Column(nullable = false) // nullを許容しない
    private String name;

    @Column(nullable = false, precision = 19, scale = 4) // 精度とスケールを指定
    private BigDecimal value; // 数値はBigDecimalを推奨

    @Column(nullable = false)
    private LocalDate date;

    private String source;

    private String unit;

    // --- コンストラクタ ---
    public EconomicIndicator() {
        // JPAにはデフォルトコンストラクタが必要
    }

    public EconomicIndicator(String name, BigDecimal value, LocalDate date, String source, String unit) {
        this.name = name;
        this.value = value;
        this.date = date;
        this.source = source;
        this.unit = unit;
    }

    // --- ゲッターとセッター ---
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public BigDecimal getValue() {
        return value;
    }

    public void setValue(BigDecimal value) {
        this.value = value;
    }

    public LocalDate getDate() {
        return date;
    }

    public void setDate(LocalDate date) {
        this.date = date;
    }

    public String getSource() {
        return source;
    }

    public void setSource(String source) {
        this.source = source;
    }

    public String getUnit() {
        return unit;
    }

    public void setUnit(String unit) {
        this.unit = unit;
    }

    // --- toString, equals, hashCode (任意ですがデバッグに便利) ---
    @Override
    public String toString() {
        return "EconomicIndicator{" +
                "id=" + id +
                ", name='" + name + '\'' +
                ", value=" + value +
                ", date=" + date +
                ", source='" + source + '\'' +
                ", unit='" + unit + '\'' +
                '}';
    }

    // equals と hashCode も実装すると良いでしょう (特にSetなどで扱う場合)
}