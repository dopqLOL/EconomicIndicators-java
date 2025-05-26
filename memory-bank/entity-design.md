# エンティティ設計ドキュメント

## 概要

このドキュメントでは、Backend Portfolio APIプロジェクトで使用するエンティティの詳細設計を記述します。
エンティティはSpring Data JPAを使用して実装され、MySQLデータベースにマッピングされます。

## エンティティ構造

### 1. EconomicIndicator（経済指標）

経済指標の基本情報を格納するエンティティです。

```java
@Entity
@Table(name = "economic_indicators")
public class EconomicIndicator {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false)
    private LocalDateTime date;
    
    @Column(length = 50, nullable = false)
    private String country;
    
    @Column(length = 100, nullable = false)
    private String indicator;
    
    @Column
    private Double actual;
    
    @Column
    private Double forecast;
    
    @Column
    private Double previous;
    
    @Column(length = 10)
    @Enumerated(EnumType.STRING)
    private Impact impact;  // HIGH, MEDIUM, LOW
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
    
    @OneToMany(mappedBy = "economicIndicator", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<VolatilityData> volatilityDataList;
    
    // Getters, Setters, コンストラクタなど
}

public enum Impact {
    HIGH, MEDIUM, LOW
}
```

### 2. VolatilityData（ボラティリティデータ）

特定の経済指標に関連するボラティリティ（価格変動）データを格納するエンティティです。

```java
@Entity
@Table(name = "volatility_data")
public class VolatilityData {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "indicator_id", nullable = false)
    private EconomicIndicator economicIndicator;
    
    @Column(length = 20, nullable = false)
    private String timeframe;
    
    @Column(name = "period_start", nullable = false)
    private LocalDateTime periodStart;
    
    @Column(name = "period_end", nullable = false)
    private LocalDateTime periodEnd;
    
    @Column(name = "high_price", nullable = false)
    private Double highPrice;
    
    @Column(name = "low_price", nullable = false)
    private Double lowPrice;
    
    @Column(nullable = false)
    private Double volatility;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
    
    // Getters, Setters, コンストラクタなど
}
```

### 3. User（ユーザー）

システムのユーザー情報を格納するエンティティです。

```java
@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(length = 50, unique = true, nullable = false)
    private String username;
    
    @Column(length = 100, unique = true, nullable = false)
    private String email;
    
    @Column(nullable = false)
    private String password;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
    
    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<UserSetting> userSettings;
    
    // Getters, Setters, コンストラクタなど
}
```

### 4. UserSetting（ユーザー設定）

ユーザーごとの設定情報を格納するエンティティです。

```java
@Entity
@Table(name = "user_settings")
public class UserSetting {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;
    
    @Column(name = "setting_key", length = 50, nullable = false)
    private String settingKey;
    
    @Column(name = "setting_value", columnDefinition = "TEXT")
    private String settingValue;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
    
    // Getters, Setters, コンストラクタなど
}
```

## エンティティ関連図

```
EconomicIndicator 1 ---- * VolatilityData
       |
       | (将来的な拡張)
       |
       v
User 1 ---- * UserSetting
```

## インデックス設計

パフォーマンスを考慮して以下のインデックスを作成します：

1. EconomicIndicator:
   - date（検索の高速化）
   - country（フィルタリング用）
   - impact（重要度でのフィルタリング用）

2. VolatilityData:
   - indicator_id（外部キー）
   - period_start, period_end（期間検索用）
   - timeframe（時間枠でのフィルタリング用）

3. User:
   - username（ログイン用）
   - email（ログイン用）

4. UserSetting:
   - user_id, setting_key（複合インデックス、特定ユーザーの特定設定検索用）

## データベースマイグレーション

初回デプロイ時およびスキーマ変更時には、Hibernateの自動スキーマ生成または手動SQLスクリプトでデータベースマイグレーションを実行します。

開発環境では以下の設定を使用：
```properties
spring.jpa.hibernate.ddl-auto=update
```

本番環境では以下の設定を使用：
```properties
spring.jpa.hibernate.ddl-auto=validate
```

## 備考

1. すべてのエンティティにcreated_atとupdated_atフィールドを含めて監査情報を記録
2. 適切なカスケード操作を設定して、関連エンティティの整合性を維持
3. LazyロードとEagerロードを適切に使い分けてパフォーマンスを最適化 