# バックエンドポートフォリオAPI - アクティブコンテキスト

**最終更新**: 2025年5月23日
**現在のフェーズ**: エンティティ層実装準備
**プロジェクト進捗率**: 10%

## 現在の焦点

### 次のフェーズ: エンティティ層実装 (Day 2: 2025年5月24日)
1. Spring Data JPAの依存関係追加
2. アプリケーション設定ファイル構成
3. ドメインモデルとJPAエンティティの実装
4. Flywayマイグレーションスクリプト作成

## エンティティ設計概要

### 1. EconomicIndicator（経済指標）
- **ドメインモデル**: `com.portfolio.backend_portfolio_api.entity.EconomicIndicator`
- **JPA エンティティ**: `com.portfolio.backend_portfolio_api.infrastructure.persistence.EconomicIndicatorJpaEntity`
- **属性**:
  - `id`: Long (主キー)
  - `date`: LocalDateTime (発表日時)
  - `country`: String (国)
  - `indicator`: String (指標名)
  - `actual`: Double (実績値)
  - `forecast`: Double (予測値)
  - `previous`: Double (前回値)
  - `impact`: Impact (高・中・低の影響度)
- **関連**:
  - `volatilityDataList`: List<VolatilityData> (1対多関連)

### 2. VolatilityData（ボラティリティデータ）
- **ドメインモデル**: `com.portfolio.backend_portfolio_api.domain.model.VolatilityData`
- **JPA エンティティ**: `com.portfolio.backend_portfolio_api.infrastructure.persistence.VolatilityDataJpaEntity`
- **属性**:
  - `id`: Long (主キー)
  - `date`: LocalDateTime (日時)
  - `high`: Double (高値)
  - `low`: Double (安値)
  - `volatility`: Double (ボラティリティ値)
  - `category`: VolatilityCategory (高・中・低のカテゴリ)
- **関連**:
  - `economicIndicator`: EconomicIndicator (多対1関連)

### 3. User（ユーザー）
- **ドメインモデル**: `com.portfolio.backend_portfolio_api.domain.model.User`
- **JPA エンティティ**: `com.portfolio.backend_portfolio_api.infrastructure.persistence.UserJpaEntity`
- **属性**:
  - `id`: Long (主キー)
  - `username`: String (ユーザー名)
  - `password`: String (パスワード)
  - `email`: String (メールアドレス)
  - `createdAt`: LocalDateTime (作成日時)
  - `updatedAt`: LocalDateTime (更新日時)
- **関連**:
  - `userSetting`: UserSetting (1対1関連)

### 4. UserSetting（ユーザー設定）
- **ドメインモデル**: `com.portfolio.backend_portfolio_api.domain.model.UserSetting`
- **JPA エンティティ**: `com.portfolio.backend_portfolio_api.infrastructure.persistence.UserSettingJpaEntity`
- **属性**:
  - `id`: Long (主キー)
  - `displaySetting`: String (表示設定)
  - `notificationSetting`: String (通知設定)
  - `updatedAt`: LocalDateTime (更新日時)
- **関連**:
  - `user`: User (1対1関連)

## テーブル設計

### economic_indicators テーブル
```sql
CREATE TABLE economic_indicators (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  date DATETIME NOT NULL,
  country VARCHAR(50) NOT NULL,
  indicator VARCHAR(100) NOT NULL,
  actual DOUBLE,
  forecast DOUBLE,
  previous DOUBLE,
  impact VARCHAR(10) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_country_date (country, date),
  INDEX idx_indicator_impact (indicator, impact)
);
```

### volatility_data テーブル
```sql
CREATE TABLE volatility_data (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  economic_indicator_id BIGINT NOT NULL,
  date DATETIME NOT NULL,
  high DOUBLE NOT NULL,
  low DOUBLE NOT NULL,
  volatility DOUBLE NOT NULL,
  category VARCHAR(10) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (economic_indicator_id) REFERENCES economic_indicators(id) ON DELETE CASCADE,
  INDEX idx_indicator_date (economic_indicator_id, date)
);
```

### users テーブル
```sql
CREATE TABLE users (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  email VARCHAR(100) NOT NULL UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### user_settings テーブル
```sql
CREATE TABLE user_settings (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL UNIQUE,
  display_setting TEXT,
  notification_setting TEXT,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

## 優先実装項目

1. 基本的なエンティティ構造と永続化
2. ドメインモデルとJPAエンティティの分離
3. マッピング戦略の実装

## 参考リソース

- [Spring Data JPA - Reference Documentation](https://docs.spring.io/spring-data/jpa/docs/current/reference/html/)
- [Hibernate ORM Documentation](https://hibernate.org/orm/documentation/6.2/)
- [Flyway Database Migrations](https://flywaydb.org/documentation/)
- [Baeldung - JPA and Hibernate](https://www.baeldung.com/hibernate-jpa-tutorial)

## 次のステップ

1. Spring Data JPAの依存関係をpom.xmlに追加
2. application.propertiesファイルの構成
3. ドメインモデルの実装
4. JPAエンティティの実装
5. Flywayマイグレーションスクリプトの作成 