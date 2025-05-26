# 詳細実装スケジュール (5月26日 - 5月31日)

## Day 1: 2025年5月26日（月）

### テーマ: 基礎構築とDocker事始め

#### タスクリスト:
- [ ] **データベース設計:**
    - [ ] EconomicIndicator, VolatilityData, User, UserSetting 各エンティティの属性、データ型、制約の最終確認。
    - [ ] エンティティ間のリレーションシップ（一対多、多対多など）の明確化。
- [ ] **JPAエンティティ実装:**
    - [ ] `EconomicIndicator.java`, `VolatilityData.java` の作成。
    - [ ] `User.java`, `UserSetting.java` の作成。
    - [ ] 各エンティティに `@Entity`, `@Id`, `@GeneratedValue`, `@Column` などのJPAアノテーションを設定。
    - [ ] リレーションシップを `@ManyToOne`, `@OneToMany` などで設定。
- [ ] **Docker学習と初期設定:**
    - [ ] Dockerの基本概念（イメージ、コンテナ、Dockerfile、ボリューム、ポート）を理解する。
        - 参考: [Docker overview | Docker Docs](https://docs.docker.com/get-started/overview/)
    - [ ] Spring Bootアプリケーション用の基本的な `Dockerfile` を作成する。
        - Multi-stage builds を意識する（JDKでビルドし、JREで実行するなど）。
        - 参考: [Spring Boot with Docker | Spring Guides](https://spring.io/guides/gs/spring-boot-docker/)
        - 参考: [Dockerfile reference | Docker Docs](https://docs.docker.com/engine/reference/builder/)

#### 学習目標:
- Spring BootにおけるJPAエンティティの基本的な実装方法を理解する。
- Dockerfileの基本的な書き方と、Spring Bootアプリをコンテナ化する手順を理解する。

---

## Day 2: 2025年5月27日（火）

### テーマ: データアクセス層とサービス層の beginnings、Dockerイメージ化

#### タスクリスト:
- [ ] **JPAリポジトリ実装:**
    - [ ] `EconomicIndicatorRepository.java`, `VolatilityDataRepository.java`, `UserRepository.java`, `UserSettingRepository.java` を作成。
    - [ ] `JpaRepository` を継承し、基本的なCRUD操作を可能にする。
    - [ ] 必要に応じてカスタムクエリメソッドを `@Query` アノテーションで定義（最初はfindBy~など簡単なものから）。
        - 参考: [Spring Data JPA - Reference Documentation](https://docs.spring.io/spring-data/jpa/reference/jpa/query-methods.html)
- [ ] **テスト用H2データベース設定:**
    - [ ] `application-test.properties` (または `application-test.yml`) にH2データベースの設定を記述。
    - [ ] テスト実行時のみH2が使われるようにプロファイルを活用。
- [ ] **テストデータ準備:**
    - [ ] `data.sql` (H2用) または Liquibase/Flyway のようなマイグレーションツールを使って初期データを投入できるようにする。
- [ ] **EconomicIndicatorService実装:**
    - [ ] `EconomicIndicatorService.java` とそのインターフェースを作成。
    - [ ] `EconomicIndicatorRepository` をDIし、CRUD操作メソッド、基本的な検索機能を実装。
    - [ ] `@Service` アノテーション付与。
- [ ] **Dockerイメージビルドと実行:**
    - [ ] 前日作成した `Dockerfile` を使って `docker build` コマンドでイメージをビルドする。
    - [ ] `docker run` コマンドでビルドしたイメージからコンテナを起動し、アプリケーションが動作することを確認（ログや簡単なヘルスチェックエンドポイントなど）。

#### 学習目標:
- Spring Data JPAリポジトリの作成方法と基本的な使い方を理解する。
- Spring Bootにおけるサービス層の役割と基本的な実装方法を理解する。
- Dockerイメージをビルドし、ローカルでコンテナを実行する方法を習得する。

---
## Day 3: 2025年5月28日（水）
### テーマ: サービス層の拡充とCI/CDの第一歩

#### タスクリスト:
- [ ] **VolatilityDataService実装:** (CRUD、指標IDによる検索)
- [ ] **UserService, UserSettingService実装:** (ユーザー登録、ログイン、設定変更などの基本機能)
- [ ] **StatisticsService基本実装:** (平均値、中央値計算、3分類ロジックのインターフェース定義とモック実装)
- [ ] **GitHubリポジトリ作成:** プロジェクト用のリモートリポジトリを作成する。
- [ ] **GitHub Actionsの基本学習:**
    - ワークフロー、ジョブ、ステップ、アクションの概念を理解する。
    - 参考: [Understanding GitHub Actions - GitHub Docs](https://docs.github.com/en/actions/learn-github-actions/understanding-github-actions)
- [ ] **基本的なCIワークフロー作成 (`.github/workflows/ci.yml`):**
    - Javaのセットアップ (e.g., `actions/setup-java@v3`)
    - Maven/Gradleを使ったビルド (`mvn clean install` or `./gradlew build`)
    - Maven/Gradleを使ったテスト実行 (`mvn test` or `./gradlew test`)
    - プッシュやプルリクエストをトリガーにする。
    - 参考: [Building and testing Java with Maven - GitHub Docs](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-java-with-maven)

#### 学習目標:
- 複数のサービスコンポーネントの実装経験。
- GitHub Actionsの基本的な仕組みと、簡単なビルド・テスト自動化ワークフローの作成方法を理解する。

---
## Day 4: 2025年5月29日（木）
### テーマ: APIエンドポイント作成とDocker Composeによる複数コンテナ連携

#### タスクリスト:
- [ ] **DTO (Data Transfer Object) 設計と実装:**
    - APIリクエスト用DTO (`XxxRequest.java`) とレスポンス用DTO (`XxxResponse.java`) を作成。
    - Bean Validation API (`javax.validation.constraints.*`) を使った入力バリデーションをDTOに追加。
        - 参考: [Validation - Spring Boot Reference Documentation](https://docs.spring.io/spring-boot/docs/current/reference/htmlsingle/#io.validation)
- [ ] **EconomicIndicatorController実装:**
    - `@RestController`, `@RequestMapping` などのアノテーションを使用。
    - CRUD操作、検索に対応するエンドポイントを作成 (`@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`)。
    - `EconomicIndicatorService` をDIして利用。
    - 基本的な例外処理 (`@ControllerAdvice`, `@ExceptionHandler`) を導入。
        - 参考: [Error Handling - Spring Boot Reference Documentation](https://docs.spring.io/spring-boot/docs/current/reference/htmlsingle/#web.servlet.spring-mvc.error-handling)
- [ ] **VolatilityDataController実装:** 同様に実装。
- [ ] **Docker Compose学習:**
    - `docker-compose.yml` の基本的な書き方と役割を理解する。
    - 参考: [Overview of Docker Compose | Docker Docs](https://docs.docker.com/compose/overview/)
- [ ] **`docker-compose.yml` 作成:**
    - Spring Bootアプリケーションサービスを定義。
    - MySQL (またはPostgreSQL) データベースサービスを定義。
    - ボリュームマッピング、ポートフォワーディング、環境変数設定など。
    - アプリケーションがDBに接続できるようにネットワーク設定。
        - 参考: [Compose file version 3 reference | Docker Docs](https://docs.docker.com/compose/compose-file/compose-file-v3/)

#### 学習目標:
- Spring MVCを使ったREST APIコントローラーの実装方法、DTOの役割、入力バリデーション、基本的な例外処理を理解する。
- Docker Composeを使って複数のコンテナ（アプリケーションとデータベース）を連携させて起動・管理する方法を習得する。

---
## Day 5: 2025年5月30日（金）
### テーマ: CSVインポート機能とCI/CDパイプラインの強化

#### タスクリスト:
- [ ] **CSVインポート機能実装:**
    - Apache Commons CSV ライブラリを `pom.xml` に追加。
        - 参考: [Apache Commons CSV – User guide](https://commons.apache.org/proper/commons-csv/user-guide.html)
    - CSVファイルを読み込み、パースしてエンティティにマッピングするロジックをサービス層に実装。
    - ファイルアップロードを受け付けるAPIエンドポイントをコントローラーに作成 (`@PostMapping` で `MultipartFile` を受け取る)。
    - データ検証ロジック (必須項目、データ型など) を実装。
- [ ] **統計計算機能 - 3分類アルゴリズム実装:**
    - パーセンタイル (例: 33パーセンタイル、66パーセンタイル) を基準とした3分類ロジックを `StatisticsService` に実装。
- [ ] **GitHub Actionsワークフロー改善:**
    - Dockerイメージをビルドするステップを追加。
    - ビルドしたDockerイメージをコンテナレジストリ (Docker Hub, GitHub Container Registryなど) にプッシュするステップを追加。
        - シークレットを使ってレジストリの認証情報を管理する。
        - 参考: [Publishing Docker images - GitHub Docs](https://docs.github.com/en/actions/publishing-packages/publishing-docker-images)
        - 参考: [Working with the GitHub Container Registry - GitHub Docs](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

#### 学習目標:
- JavaでのCSVファイル処理方法と、Spring Bootでのファイルアップロード機能の実装方法を理解する。
- CI/CDパイプラインにDockerイメージのビルドとプッシュを組み込む方法を習得する。

---
## Day 6: 2025年5月31日（土）
### テーマ: 統計機能拡充、テスト、最適化、ドキュメント、CI/CD最終調整

#### タスクリスト:
- [ ] **統計計算機能 - 時間帯ボラティリティ計算:**
    - 特定の時間帯におけるボラティリティデータを集計・計算する機能を `StatisticsService` に実装。
- [ ] **統計計算機能 - 地合い判断ロジック:**
    - 直近の複数指標データから市場の地合いを簡易的に判断するロジックを `StatisticsService` に実装 (これはスコープと相談)。
- [ ] **テスト強化:**
    - JUnit5 と Mockito を使った単体テストの拡充 (サービスクラス、コントローラークラス)。
        - 参考: [Testing - Spring Boot Reference Documentation](https://docs.spring.io/spring-boot/docs/current/reference/htmlsingle/#testing)
    - Spring Boot Test を使った統合テスト (`@SpringBootTest`) の作成。
    - Postman (または同様のツール) を使ってAPIエンドポイントの動作確認と簡単なテストコレクション作成。
- [ ] **パフォーマンス最適化検討:**
    - 複雑なクエリの実行計画を確認 (DBツールや `EXPLAIN` を利用)。
    - 必要な箇所へのインデックス追加を検討。
    - (この段階では深入りせず、ボトルネックになりそうな箇所の特定と改善案の考察程度)
- [ ] **ドキュメント整備:**
    - `README.md` にプロジェクト概要、起動方法 (Docker Compose利用)、APIエンドポイント一覧などを更新。
    - 簡単なAPIドキュメントの概要を作成 (Swagger/OpenAPI の導入検討も良いが、まずは手動で)。
- [ ] **CI/CDパイプラインの最終確認:**
    - GitHub Actionsのワークフローが意図通りに動作することを確認。
    - ビルド、テスト、イメージプッシュが成功することを確認。

#### 学習目標:
- より複雑なビジネスロジックの実装経験。
- Spring Bootアプリケーションにおけるテスト戦略と各種テストの実装方法を理解する。
- パフォーマンス最適化の基本的な考え方とアプローチを理解する。
- プロジェクトのドキュメンテーションの重要性と基本的な作成方法を理解する。
- CI/CDパイプライン全体の流れを把握し、安定動作を確認する。 