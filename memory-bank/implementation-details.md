# 実装詳細ドキュメント

## プロジェクト実装における段階的アプローチ

このドキュメントでは、Backend Portfolio APIプロジェクトの各実装段階における詳細を記述します。

## 日次実装詳細

### Day 1: 2025年5月23日（金）- データベース設計完了

#### 目標
- プロジェクト計画の再確認
- データベースモデル設計の最終確認
- 実装に必要なドキュメント作成

#### 成果物
- tasks.md: 詳細な実装計画と日程
- entity-design.md: エンティティ設計ドキュメント
- learning-notes.md: 学習内容記録用テンプレート
- daily-reflection.md: 日次振り返り用テンプレート

### Day 2: 2025年5月24日（土）- エンティティ層実装

#### 目標
- JPA依存関係追加と設定
- エンティティクラス実装
- データベース接続設定

#### タスク詳細

1. **POM.xmlの更新**
   - Spring Data JPA、MySQL Connector、H2 Database依存関係追加

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-jpa</artifactId>
</dependency>
<dependency>
    <groupId>mysql</groupId>
    <artifactId>mysql-connector-java</artifactId>
    <scope>runtime</scope>
</dependency>
<dependency>
    <groupId>com.h2database</groupId>
    <artifactId>h2</artifactId>
    <scope>test</scope>
</dependency>
```

2. **Application.propertiesの設定**
   - 開発環境用DB設定
   - H2テスト環境設定

```properties
# 開発環境データベース設定
spring.datasource.url=jdbc:mysql://localhost:3306/portfolio_api?useSSL=false&serverTimezone=UTC
spring.datasource.username=root
spring.datasource.password=password
spring.datasource.driver-class-name=com.mysql.cj.jdbc.Driver

# JPA設定
spring.jpa.hibernate.ddl-auto=update
spring.jpa.show-sql=true
spring.jpa.properties.hibernate.format_sql=true
spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.MySQL8Dialect

# テスト用H2設定（プロファイル: test）
# spring.datasource.url=jdbc:h2:mem:testdb
# spring.datasource.username=sa
# spring.datasource.password=
# spring.datasource.driver-class-name=org.h2.Driver
# spring.jpa.database-platform=org.hibernate.dialect.H2Dialect
```

3. **エンティティクラス実装**
   - com.portfolio.backend_portfolio_api.entity パッケージ作成
   - entity-design.mdに基づいた各エンティティクラス実装
   - JPA関連アノテーション付与

4. **リレーション設定**
   - エンティティ間の関連付け（@OneToMany、@ManyToOne等）
   - カスケード処理設定

### Day 3: 2025年5月25日（日）- リポジトリ層実装

#### 目標
- リポジトリインターフェース実装
- テストデータ作成
- リポジトリテスト実装

#### タスク詳細

1. **リポジトリインターフェース実装**
   - com.portfolio.backend_portfolio_api.repository パッケージ作成
   - 各エンティティのJpaRepositoryインターフェース実装
   
```java
public interface EconomicIndicatorRepository extends JpaRepository<EconomicIndicator, Long> {
    List<EconomicIndicator> findByCountry(String country);
    List<EconomicIndicator> findByDateBetween(LocalDateTime start, LocalDateTime end);
    List<EconomicIndicator> findByImpact(Impact impact);
    // その他必要なクエリメソッド
}
```

2. **テストデータ作成**
   - src/test/resources/data.sql に初期データ作成

```sql
-- テスト用経済指標データ
INSERT INTO economic_indicators (date, country, indicator, actual, forecast, previous, impact, created_at, updated_at) 
VALUES 
('2025-05-20 10:00:00', 'USA', 'Non-Farm Employment Change', 250.5, 220.0, 210.0, 'HIGH', NOW(), NOW()),
('2025-05-21 15:30:00', 'EUR', 'ECB Interest Rate Decision', 4.25, 4.25, 4.0, 'HIGH', NOW(), NOW()),
('2025-05-22 08:45:00', 'JPY', 'Monetary Policy Statement', NULL, NULL, NULL, 'MEDIUM', NOW(), NOW());

-- テスト用ボラティリティデータ
INSERT INTO volatility_data (indicator_id, timeframe, period_start, period_end, high_price, low_price, volatility, created_at, updated_at)
VALUES
(1, '2hours', '2025-05-20 10:00:00', '2025-05-20 12:00:00', 1.1250, 1.1150, 0.0100, NOW(), NOW()),
(2, '2hours', '2025-05-21 15:30:00', '2025-05-21 17:30:00', 1.0870, 1.0790, 0.0080, NOW(), NOW()),
(3, '2hours', '2025-05-22 08:45:00', '2025-05-22 10:45:00', 157.50, 156.20, 1.3000, NOW(), NOW());
```

3. **リポジトリテスト実装**
   - 各リポジトリのテストクラス作成
   - 基本CRUD操作とカスタムクエリメソッドのテスト

### Day 4以降の実装予定は、進捗に応じて更新していきます。

## APIエンドポイント設計

### 1. 経済指標API

| メソッド | URL                              | 説明                         |
|----------|----------------------------------|------------------------------|
| GET      | /api/indicators                  | 全経済指標取得               |
| GET      | /api/indicators/{id}             | 指定ID経済指標取得           |
| GET      | /api/indicators/search           | 条件検索（日付、国、重要度） |
| POST     | /api/indicators                  | 新規経済指標登録             |
| PUT      | /api/indicators/{id}             | 経済指標更新                 |
| DELETE   | /api/indicators/{id}             | 経済指標削除                 |
| POST     | /api/indicators/import           | CSVデータインポート          |

### 2. ボラティリティAPI

| メソッド | URL                                  | 説明                              |
|----------|--------------------------------------|---------------------------------|
| GET      | /api/volatilities                    | 全ボラティリティデータ取得        |
| GET      | /api/volatilities/{id}               | 指定IDデータ取得                 |
| GET      | /api/volatilities/indicator/{id}     | 指定経済指標のデータ全取得        |
| GET      | /api/volatilities/statistics/{id}    | 指定経済指標の統計情報取得        |
| POST     | /api/volatilities                    | 新規データ登録                   |
| PUT      | /api/volatilities/{id}               | データ更新                       |
| DELETE   | /api/volatilities/{id}               | データ削除                       |

### 3. ユーザーAPI

| メソッド | URL                                | 説明                          |
|----------|------------------------------------|-------------------------------|
| GET      | /api/users                         | 全ユーザー取得                |
| GET      | /api/users/{id}                    | 指定ID取得                    |
| POST     | /api/users                         | ユーザー登録                  |
| PUT      | /api/users/{id}                    | ユーザー更新                  |
| DELETE   | /api/users/{id}                    | ユーザー削除                  |
| GET      | /api/users/{id}/settings           | 指定ユーザーの全設定取得      |
| GET      | /api/users/{id}/settings/{key}     | 指定ユーザーの特定設定取得    |
| POST     | /api/users/{id}/settings           | 設定追加                      |
| PUT      | /api/users/{id}/settings/{key}     | 設定更新                      |
| DELETE   | /api/users/{id}/settings/{key}     | 設定削除                      |

## データ処理フロー

1. MQL5スクリプトから経済指標データをCSVとして出力
2. CSVファイルをAPIを通じてインポート
3. Spring Bootバックエンドでデータ処理
4. 必要に応じて統計計算処理を適用
5. RESTful APIを通じてクライアントにデータを提供

## 将来的な拡張

1. クライアントサイド実装（React/Angular/Vue等）
2. リアルタイムデータ更新（WebSockets）
3. 高度な統計分析機能
4. チャート表示機能 