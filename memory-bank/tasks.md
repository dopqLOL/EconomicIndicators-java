# バックエンドポートフォリオAPI - タスク管理

## プロジェクト概要
- **プロジェクト名**: 経済指標・ボラティリティ分析 REST API
- **期間**: 2025年5月23日 - 2025年6月1日
- **目的**: 経済指標とボラティリティデータを管理・分析するバックエンドシステム構築

## 日次タスクリスト

### 2025年5月23日（金） - Day 1: プロジェクト計画・設計
- [x] プロジェクト計画書作成
- [x] 技術スタックの選定と詳細化
- [x] アーキテクチャ設計 (ヘキサゴナルアーキテクチャ)
- [x] データベーススキーマ設計
- [x] エンティティ関連図作成
- [x] API エンドポイント設計
- [x] コーディング規約の策定
- [x] テスト戦略の立案
- [x] リスクと対策の検討
- [x] 日次振り返りの実施
- [x] 実装計画のアーカイブ

### 2025年5月24日（土） - Day 2: エンティティ層実装
- [ ] Spring Data JPAの依存関係追加
- [ ] アプリケーション設定ファイル(application.properties)の構成
  - [ ] データベース接続設定
  - [ ] JPA設定
  - [ ] Hibernate設定
- [x] Domain層の実装
  - [x] EconomicIndicator ドメインモデル
  - [x] VolatilityData ドメインモデル
  - [x] User ドメインモデル
  - [x] UserSetting ドメインモデル
- [ ] Infrastructure層の実装
  - [ ] EconomicIndicatorJpaEntity
  - [ ] VolatilityDataJpaEntity
  - [ ] UserJpaEntity
  - [ ] UserSettingJpaEntity
- [ ] Flyway マイグレーションスクリプト作成
  - [ ] V1.0.0__create_initial_schema.sql
- [ ] テスト用の設定ファイル (application-test.properties)
- [ ] 日次振り返りの実施
- [x] **エンティティ間のリレーション設定** (旧Day 2)

### 進捗状況
- **全体進捗**: 10% (計画通り)
- **最終更新日**: 2025年5月23日
- **次のマイルストーン**: エンティティ層の実装（5月24日）

## タスク優先度マトリックス

### 高優先度 / 高緊急度
- Spring Data JPAの依存関係追加
- EconomicIndicatorドメインモデルの実装
- アプリケーション設定ファイルの構成

### 高優先度 / 低緊急度
- テスト用の設定ファイル作成
- VolatilityDataドメインモデルの実装

### 低優先度 / 高緊急度
- マイグレーションスクリプト作成

### 低優先度 / 低緊急度
- User関連モデルの実装

## リソース・参考資料
- [Spring Data JPA - Reference Documentation](https://docs.spring.io/spring-data/jpa/docs/current/reference/html/)
- [Flyway Documentation](https://flywaydb.org/documentation/)
- [Hibernate ORM Documentation](https://hibernate.org/orm/documentation/)

# Backend Portfolio API - 実装計画 (2025.05.23 - 2025.06.01)

## 📅 現状と目標

**開始日**: 2025年5月23日（金）
**目標期限**: 2025年6月1日（日）
**残り日数**: 9日間

## 🎯 短期実装計画 (5月26日 - 5月31日)

### Day 1: 2025年5月26日（月）- DB設計、エンティティ、Docker初期設定
- **推奨ブランチ**: `feature/day1-db-entity-docker`
- [x] **DB設計最終確認** (旧Day 1)
- [x] **EconomicIndicator, VolatilityDataエンティティ実装** (旧Day 2)
- [x] **User, UserSettingエンティティ実装** (旧Day 2)
- [x] **エンティティ間のリレーション設定** (旧Day 2)
- [x] **Docker環境構築準備:** Docker Desktopインストール確認、基本的なDockerコマンド学習
- [x] **Spring BootアプリのDockerfile作成 (初期)**

### Day 2: 2025年5月27日（火）- リポジトリ層、サービス層(基本)、Dockerイメージビルド
- **推奨ブランチ**: `feature/day2-repo-service-docker`
- [ ] **各エンティティのリポジトリインターフェース実装** (旧Day 3)
- [ ] **テスト用H2データベース設定** (旧Day 2) および **テスト用データセット作成とインポートスクリプト実装** (旧Day 3)
- [ ] **EconomicIndicatorService実装 (CRUD、基本検索)** (旧Day 4)
- [ ] **Dockerイメージビルドとローカルコンテナ実行確認**

### Day 3: 2025年5月28日（水）- サービス層(応用)、CI/CD初期設定
- **推奨ブランチ**: `feature/day3-service-cicd`
- [ ] **VolatilityDataService実装 (CRUD、指標ID検索)** (旧Day 4)
- [ ] **UserService, UserSettingService実装 (基本機能)** (旧Day 5)
- [ ] **StatisticsService基本実装 (平均値・中央値、3分類ロジック基本)** (旧Day 5)
- [ ] **CI/CD導入準備:** GitHub Actionsの基本学習、リポジトリ作成
- [ ] **簡単なビルドとテストを実行するGitHub Actionsワークフロー作成 (初期)**

### Day 4: 2025年5月29日（木）- コントローラー層、DTO設計、Docker Compose
- **推奨ブランチ**: `feature/day4-controller-dto-compose`
- [ ] **APIリクエスト/レスポンスDTOクラス設計** (旧Day 6)
- [ ] **EconomicIndicatorController実装 (CRUD、検索、基本例外処理)** (旧Day 6)
- [ ] **VolatilityDataController実装 (CRUD、指標ID検索)** (旧Day 7)
- [ ] **Docker Compose導入:** アプリケーションとMySQLデータベースを連携させる `docker-compose.yml` 作成

### Day 5: 2025年5月30日（金）- CSVインポート、統計計算(3分類)、CI/CD改善
- **推奨ブランチ**: `feature/day5-csv-stats-cicd`
- [ ] **CSVファイル読み込み機構実装 (Apache Commons CSV)** (旧Day 8)
- [ ] **インポートAPIエンドポイント実装 (ファイルアップロード、データ検証)** (旧Day 8)
- [ ] **3分類アルゴリズム詳細実装 (パーセンタイルベース)** (旧Day 9)
- [ ] **GitHub Actionsワークフロー改善:** Dockerイメージビルドとプッシュ (例: Docker Hub, GitHub Container Registry) を追加

### Day 6: 2025年5月31日（土）- 統計計算(応用)、テスト、最適化、ドキュメント
- **推奨ブランチ**: `feature/day6-stats-test-optimize`
- [ ] **時間帯ボラティリティ計算実装** (旧Day 9)
- [ ] **地合い判断ロジック実装** (旧Day 9)
- [ ] **単体テスト・統合テスト強化、API統合テスト(Postman)** (旧Day 7, Day 10)
- [ ] **パフォーマンス最適化検討 (クエリ、インデックス)** (旧Day 10)
- [ ] **ドキュメント整備 (README更新、APIドキュメント概要作成)** (旧Day 10)
- [ ] **CI/CDパイプラインの動作確認と最終調整**

## 📚 学習トラッキング

### 学習ノート

各実装ステップで学んだ内容を以下の形式で記録：

```markdown
# [日付] - [実装内容]

## 学んだ概念/技術
- 概念1: 詳細説明
- 概念2: 詳細説明

## 実装上の課題と解決策
- 課題1: 解決策
- 課題2: 解決策

## 次回のための改善点
- 改善点1
- 改善点2
```

### 学習リソース

- [Spring Boot 公式ドキュメント](https://spring.io/projects/spring-boot)
- [Baeldung Spring チュートリアル](https://www.baeldung.com)
- [Spring Data JPA ガイド](https://spring.io/guides/gs/accessing-data-jpa/)
- [RESTful Web Services ベストプラクティス](https://www.baeldung.com/rest-api-best-practices-design)
- [Docker Documentation](https://docs.docker.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## 🏆 成功指標

### Day 2終了時点
- [ ] すべてのエンティティとリポジトリが実装されている
- [ ] アプリケーションがDockerコンテナとしてローカルで実行できる
- [ ] テストデータをH2データベースに読み込める

### Day 4終了時点
- [ ] 基本的なCRUD操作が可能なAPIが実装されている
- [ ] APIリクエスト/レスポンスが適切に構造化されている
- [ ] Docker ComposeでアプリとDBが連携して動作する

### Day 6終了時点
- [ ] CSVインポート機能が動作する
- [ ] 統計計算機能（3分類、平均値、中央値、時間帯ボラティリティ）が実装されている
- [ ] 基本的なテストケースが通過する
- [ ] README更新とAPIドキュメント概要が整備されている
- [ ] 基本的なCI/CDパイプライン (ビルド、テスト、イメージプッシュ) が動作する

## 📝 デイリー振り返り

各日の終わりに5-10分間で以下の項目を記録：

1. 今日の成果：
2. 直面した課題：
3. 解決策/学び：
4. 明日の目標：
5. 必要な調査/学習：

# 📑 実装詳細

## データベースモデル

```
EconomicIndicator {
    id: Long (PK)
    date: LocalDateTime
    country: String
    indicator: String
    actual: Double
    forecast: Double
    previous: Double
    impact: String (HIGH, MEDIUM, LOW)
    created_at: LocalDateTime
    updated_at: LocalDateTime
}

VolatilityData {
    id: Long (PK)
    indicator_id: Long (FK -> EconomicIndicator)
    timeframe: String
    period_start: LocalDateTime
    period_end: LocalDateTime
    high_price: Double
    low_price: Double
    volatility: Double
    created_at: LocalDateTime
    updated_at: LocalDateTime
}

User {
    id: Long (PK)
    username: String
    email: String
    password: String (hashed)
    created_at: LocalDateTime
    updated_at: LocalDateTime
}

UserSetting {
    id: Long (PK)
    user_id: Long (FK -> User)
    setting_key: String
    setting_value: String
    created_at: LocalDateTime
    updated_at: LocalDateTime
}
```

## パッケージ構造

```
com.portfolio.backend_portfolio_api
├── config/                    # 設定クラス
│   ├── SecurityConfig.java    # セキュリティ設定
│   ├── SwaggerConfig.java     # API文書設定
│   └── WebConfig.java         # Web関連設定
├── controller/                # API制御層
│   ├── EconomicController.java
│   ├── VolatilityController.java
│   └── UserController.java
├── dto/                       # データ転送オブジェクト
│   ├── request/
│   └── response/
├── entity/                    # データモデル
│   ├── EconomicIndicator.java
│   ├── VolatilityData.java
│   └── User.java
├── repository/                # データアクセス層
│   ├── EconomicRepository.java
│   ├── VolatilityRepository.java
│   └── UserRepository.java
├── service/                   # ビジネス層
│   ├── EconomicService.java
│   ├── VolatilityService.java
│   ├── UserService.java
│   └── StatisticsService.java
├── util/                      # ユーティリティ
│   ├── CsvImporter.java
│   ├── CalculationUtil.java
│   └── JwtUtil.java
└── BackendPortfolioApiApplication.java
```

## 学習対象技術

1. **Spring Boot基礎**:
   - アプリケーション構成
   - 依存性注入
   - アプリケーションプロパティ

2. **Spring Data JPA**:
   - エンティティライフサイクル
   - リポジトリパターン
   - カスタムクエリ作成

3. **REST API設計**:
   - リソース設計
   - HTTPメソッド活用
   - ステータスコード適切な使用

4. **データ処理**:
   - CSVファイル読み込み
   - データ変換と検証
   - 統計計算アルゴリズム
