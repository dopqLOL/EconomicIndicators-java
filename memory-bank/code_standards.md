# バックエンドエンジニア採用を見据えたコーディング規約

## 1. コード品質の基本原則

### 読みやすさと保守性
- **シンプルさ**: 複雑な実装より単純な実装を優先する
- **明確さ**: 意図が明確に伝わるコードを書く
- **一貫性**: プロジェクト全体で一貫したスタイルとパターンを使用する
- **自己文書化**: コードそのものが説明的であるように書く
- **SOLID原則**: 単一責任、オープン・クローズド、リスコフの置換、インターフェイス分離、依存性逆転の原則を適用

### バグ防止
- **防御的プログラミング**: 入力値検証を常に行う
- **不変性の優先**: 可能な限りイミュータブルなオブジェクトを使用
- **副作用の最小化**: 関数やメソッドの副作用を明示的に制限
- **例外処理の一貫性**: 例外処理のパターンを統一
- **早期検証とフェイルファスト**: 問題を早期に検出して例外をスローする

## 2. 命名規則

### クラスとインターフェース
- **PascalCase**: 先頭大文字のキャメルケースを使用 (`EconomicIndicator`, `VolatilityService`)
- **名詞または名詞句**: クラスは名詞または名詞句で表現 (`User`, `IndicatorService`)
- **インターフェース命名**: 機能を表す形容詞またはable接尾辞 (`Searchable`, `Cacheable`)
- **抽象クラス**: 接頭辞にAbstractを付ける (`AbstractEntity`, `AbstractService`)
- **実装クラス**: インターフェース名+Implの形式 (`SearchServiceImpl`)

### メソッド
- **camelCase**: 先頭小文字のキャメルケース (`calculateVolatility`, `findByCountry`)
- **動詞または動詞句**: 動作を表す (`save`, `findById`, `calculateTotal`)
- **ブーリアンメソッド**: is, has, canなどの接頭辞 (`isValid`, `hasPermission`)
- **ゲッター/セッター**: get/setの接頭辞 (`getName`, `setAge`) - Lombokの使用推奨

### 変数とフィールド
- **camelCase**: 先頭小文字のキャメルケース (`userName`, `economicData`)
- **具体的な名前**: 抽象的な名前を避ける (`data` ではなく `volatilityData`)
- **ハンガリアン表記法の回避**: 型を名前に含めない (`strName` ではなく `name`)
- **省略形の回避**: 完全な単語を使用 (`usr` ではなく `user`)

### 定数
- **UPPER_SNAKE_CASE**: すべて大文字でアンダースコア区切り (`MAX_RETRY_COUNT`, `API_BASE_URL`)
- **static final**: すべての定数はstatic finalで宣言

### パッケージ
- **すべて小文字**: ドメイン逆順の形式 (`com.portfolio.backend_portfolio_api`)
- **単一責任**: 各パッケージは単一の責任や機能を持つ
- **階層構造**: 機能やレイヤーで論理的に区分 (`controller`, `service`, `repository`)

## 3. コード構造と編成

### クラス構造
- **最大行数**: 500行を超えるクラスは分割を検討
- **メンバー順序**:
  1. 静的フィールド
  2. インスタンスフィールド
  3. コンストラクタ
  4. 公開メソッド
  5. 保護メソッド
  6. 非公開メソッド
  7. 内部クラス

### メソッド構造
- **最大行数**: 30行を超えるメソッドは分割を検討
- **単一責任**: 各メソッドは1つのタスクのみを実行
- **パラメータ数**: 最大3つ、それ以上は専用クラスやDTOを使用
- **抽象化レベル**: メソッド内では同レベルの抽象化を維持

### コメント規約
- **Javadoc**:
  ```java
  /**
   * 経済指標と日付範囲に基づいてボラティリティデータを検索
   *
   * @param indicatorId 検索対象の経済指標ID
   * @param startDate 検索開始日 (含む)
   * @param endDate 検索終了日 (含む)
   * @return ボラティリティデータのリスト
   * @throws IllegalArgumentException 日付範囲が無効な場合
   */
  List<VolatilityData> findByIndicatorAndDateRange(Long indicatorId, LocalDateTime startDate, LocalDateTime endDate);
  ```

- **実装コメント**:
  ```java
  // 3分類（大・中・小）に分類するために33パーセンタイルと67パーセンタイルを計算
  double lowerThreshold = calculatePercentile(volatilityValues, 33);
  double upperThreshold = calculatePercentile(volatilityValues, 67);
  ```

- **TODOコメント**:
  ```java
  // TODO: パフォーマンスを改善するためにキャッシュを実装する
  ```

## 4. Spring Boot特有の規約

### 依存性注入
- **コンストラクタ注入**: フィールド注入よりもコンストラクタ注入を優先
  ```java
  // 推奨
  @Service
  public class EconomicIndicatorServiceImpl implements EconomicIndicatorService {
      private final EconomicIndicatorRepository repository;
  
      @Autowired // コンストラクタが1つの場合は省略可
      public EconomicIndicatorServiceImpl(EconomicIndicatorRepository repository) {
          this.repository = repository;
      }
  }
  
  // 非推奨
  @Service
  public class EconomicIndicatorServiceImpl implements EconomicIndicatorService {
      @Autowired
      private EconomicIndicatorRepository repository;
  }
  ```

- **インターフェースによる緩い結合**: 実装ではなくインターフェースに依存
  ```java
  // 推奨
  private final EconomicIndicatorService service;
  
  // 非推奨
  private final EconomicIndicatorServiceImpl service;
  ```

### コンポーネント分離
- **コントローラー**:
  - リクエスト処理とレスポンス生成のみを担当
  - ビジネスロジックを含めない
  - 入力検証とエラーハンドリングを一貫して実施

- **サービス**:
  - ビジネスロジックを集約
  - トランザクション境界を定義
  - リポジトリ呼び出しを調整

- **リポジトリ**:
  - データアクセスのみを担当
  - クエリメソッド命名規則を統一
  - パフォーマンスを考慮したクエリ設計

### JPA/Hibernate
- **エンティティ設計**:
  - `@Entity`、`@Table`、`@Column`アノテーションの一貫した使用
  - 関連の明示的な宣言（`@OneToMany`、`@ManyToOne`など）
  - 双方向関連の場合、所有側と非所有側の明確な区別

- **N+1問題の回避**:
  - `@EntityGraph`を使用した関連エンティティのフェッチ
  - 必要に応じて`@Query`でJPQLクエリを最適化

### RESTful API設計
- **URI設計**:
  - リソース名は複数形名詞: `/api/indicators`
  - ID指定: `/api/indicators/{id}`
  - サブリソース: `/api/indicators/{id}/volatilities`
  - クエリパラメータ: `/api/indicators?country=US&date=2025-05-24`

- **HTTPメソッド**:
  - GET: リソース取得（安全かつべき等）
  - POST: リソース作成
  - PUT: リソース全体更新
  - PATCH: リソース部分更新
  - DELETE: リソース削除

- **ステータスコード**:
  - 200 OK: 正常処理
  - 201 Created: リソース作成成功
  - 204 No Content: 正常処理（返却データなし）
  - 400 Bad Request: リクエスト形式不正
  - 401 Unauthorized: 認証失敗
  - 403 Forbidden: 権限不足
  - 404 Not Found: リソース不存在
  - 500 Internal Server Error: サーバーエラー

- **統一レスポンス形式**:
  ```json
  {
    "status": "success",
    "data": { ... },
    "message": "操作が正常に完了しました"
  }
  ```

## 5. エラー処理

### 例外処理
- **カスタム例外**: ドメイン固有の例外クラスを定義
  ```java
  public class ResourceNotFoundException extends RuntimeException {
      private final String resourceName;
      private final String fieldName;
      private final Object fieldValue;
  
      public ResourceNotFoundException(String resourceName, String fieldName, Object fieldValue) {
          super(String.format("%s not found with %s : '%s'", resourceName, fieldName, fieldValue));
          this.resourceName = resourceName;
          this.fieldName = fieldName;
          this.fieldValue = fieldValue;
      }
  }
  ```

- **集中例外処理**: `@ControllerAdvice`による統一的な例外ハンドリング
  ```java
  @ControllerAdvice
  public class GlobalExceptionHandler {
      @ExceptionHandler(ResourceNotFoundException.class)
      public ResponseEntity<ErrorResponse> handleResourceNotFoundException(ResourceNotFoundException ex) {
          ErrorResponse error = new ErrorResponse(
              HttpStatus.NOT_FOUND.value(),
              ex.getMessage(),
              Instant.now()
          );
          return new ResponseEntity<>(error, HttpStatus.NOT_FOUND);
      }
  }
  ```

### バリデーション
- **Bean Validation**: JSR-380アノテーションの使用
  ```java
  public class IndicatorDTO {
      @NotBlank(message = "国名は必須です")
      @Size(max = 50, message = "国名は50文字以内で入力してください")
      private String country;
  
      @NotBlank(message = "指標名は必須です")
      @Size(max = 100, message = "指標名は100文字以内で入力してください")
      private String indicator;
  
      @NotNull(message = "日時は必須です")
      private LocalDateTime date;
  }
  ```

- **カスタムバリデーション**: 複雑な検証ロジック用のカスタムアノテーション
  ```java
  @Target({ElementType.FIELD})
  @Retention(RetentionPolicy.RUNTIME)
  @Constraint(validatedBy = ImpactValidator.class)
  public @interface ValidImpact {
      String message() default "影響度は HIGH, MEDIUM, LOW のいずれかである必要があります";
      Class<?>[] groups() default {};
      Class<? extends Payload>[] payload() default {};
  }
  ```

## 6. テスト規約

### テスト命名
- **given_when_then形式**: テストシナリオを明確に表現
  ```java
  @Test
  void givenValidEconomicIndicator_whenSave_thenSuccess() { ... }
  
  @Test
  void givenNonExistentId_whenFindById_thenThrowResourceNotFoundException() { ... }
  ```

### テスト構造
- **Arrange-Act-Assert (AAA)**: テストを3つの区分に分ける
  ```java
  @Test
  void givenValidData_whenCalculateVolatility_thenCorrectResult() {
      // Arrange
      double highPrice = 1.2050;
      double lowPrice = 1.1950;
      
      // Act
      double volatility = calculationService.calculateVolatility(highPrice, lowPrice);
      
      // Assert
      assertEquals(0.01, volatility, 0.0001);
  }
  ```

### モックの使用
- **Mockito**: 外部依存のモック化
  ```java
  @ExtendWith(MockitoExtension.class)
  class EconomicIndicatorServiceTest {
      @Mock
      private EconomicIndicatorRepository repository;
      
      @InjectMocks
      private EconomicIndicatorServiceImpl service;
      
      @Test
      void givenExistingId_whenFindById_thenReturnEconomicIndicator() {
          // Arrange
          EconomicIndicator indicator = new EconomicIndicator();
          indicator.setId(1L);
          when(repository.findById(1L)).thenReturn(Optional.of(indicator));
          
          // Act
          EconomicIndicator result = service.findById(1L);
          
          // Assert
          assertNotNull(result);
          assertEquals(1L, result.getId());
          verify(repository).findById(1L);
      }
  }
  ```

### テストカバレッジ
- **カバレッジ目標**:
  - サービス層: 90%以上
  - リポジトリ層: 85%以上
  - ドメインモデル: 95%以上
  - コントローラー層: 80%以上
  - 全体: 80%以上

## 7. パフォーマンスと最適化

### データベースアクセス
- **インデックス**: 頻繁に検索される列にインデックスを適用
- **エスケープSQL**: インデックスを無効化するような関数適用を回避
- **ページネーション**: 大量データ取得時には必ずページネーションを適用
- **バルク操作**: 複数レコードの処理にはバッチ処理を使用

### キャッシュ
- **Spring Cache**: 適切なキャッシュ戦略と有効期限設定
  ```java
  @Cacheable(value = "indicators", key = "#id")
  public EconomicIndicator findById(Long id) {
      return repository.findById(id)
              .orElseThrow(() -> new ResourceNotFoundException("EconomicIndicator", "id", id));
  }
  
  @CacheEvict(value = "indicators", key = "#indicator.id")
  public EconomicIndicator update(EconomicIndicator indicator) {
      return repository.save(indicator);
  }
  ```

### 非同期処理
- **@Async**: 長時間実行タスクの非同期実行
  ```java
  @Async
  public CompletableFuture<List<VolatilityData>> calculateHistoricalVolatility(Long indicatorId) {
      // 長時間かかる計算処理
      List<VolatilityData> results = performCalculation(indicatorId);
      return CompletableFuture.completedFuture(results);
  }
  ```

# アーキテクチャ設計文書

## 1. アーキテクチャ概要

本プロジェクトは、保守性、拡張性、テスト容易性を考慮して**ヘキサゴナルアーキテクチャ（ポートとアダプター）**のアプローチを採用します。これにより、ビジネスロジックと技術的実装の分離、および依存関係の明確な管理を実現します。

## 2. アーキテクチャの層構造

```
com.portfolio.backend_portfolio_api
├── application/        # ユースケース実装（アプリケーションサービス）
│   ├── dto/            # データ転送オブジェクト
│   └── service/        # アプリケーションサービス
├── domain/             # ドメインモデルとロジック
│   ├── model/          # ビジネスエンティティ
│   ├── service/        # ドメインサービス
│   └── repository/     # リポジトリインターフェース
├── infrastructure/     # 技術的実装詳細
│   ├── persistence/    # データベースアクセス実装
│   ├── external/       # 外部サービス連携
│   ├── config/         # 設定クラス
│   └── security/       # セキュリティ実装
└── interfaces/         # 外部とのインターフェース
    ├── rest/           # REST APIコントローラー
    ├── scheduler/      # スケジュールされたタスク
    └── exception/      # 例外ハンドリング
```

## 3. レイヤー間の依存関係

依存関係の方向: interfaces → application → domain ← infrastructure

```
interfaces ──────┐
                 ↓
application ─────┐
                 ↓
domain ←─────────┘
  ↑
infrastructure ──┘
```

この構造により、ドメイン層は他のどの層にも依存せず、最も重要なビジネスルールを純粋に保ちます。

## 4. CQRS原則の部分適用

コマンド（書き込み操作）とクエリ（読み取り操作）の分離を行い、それぞれの最適化を図ります。

### 4.1 コマンドサービス
```java
@Service
public class EconomicIndicatorCommandService {
    private final EconomicIndicatorRepository repository;
    
    public EconomicIndicator create(EconomicIndicatorCreateCommand command) { ... }
    public EconomicIndicator update(EconomicIndicatorUpdateCommand command) { ... }
    public void delete(Long id) { ... }
}
```

### 4.2 クエリサービス
```java
@Service
public class EconomicIndicatorQueryService {
    private final EconomicIndicatorRepository repository;
    
    public EconomicIndicatorDTO findById(Long id) { ... }
    public PagedResult<EconomicIndicatorDTO> findByCountry(String country, Pageable pageable) { ... }
    public List<StatisticsDTO> getVolatilityStatistics(Long indicatorId) { ... }
}
```

## 5. ドメインモデルとエンティティ

### 5.1 ドメインエンティティ
ドメインエンティティはビジネスルールとロジックを含み、技術的な詳細（JPA等）を含めません。

```java
// ドメインモデル
public class EconomicIndicator {
    private Long id;
    private LocalDateTime date;
    private String country;
    private String indicator;
    private Double actual;
    private Double forecast;
    private Double previous;
    private Impact impact;
    private List<VolatilityData> volatilityDataList;
    
    // ビジネスロジック
    public boolean isHighImpact() {
        return Impact.HIGH.equals(this.impact);
    }
    
    public boolean hasActualValue() {
        return actual != null;
    }
    
    public double calculateSurprise() {
        if (actual == null || forecast == null) return 0;
        return actual - forecast;
    }
}
```

### 5.2 永続化エンティティ
技術的な詳細（JPA等）を含む、データベース用のエンティティ。

```java
// インフラストラクチャ層のJPAエンティティ
@Entity
@Table(name = "economic_indicators")
public class EconomicIndicatorJpaEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false)
    private LocalDateTime date;
    
    @Column(length = 50, nullable = false)
    private String country;
    
    // 他のフィールド...
    
    // マッピングメソッド
    public EconomicIndicator toDomainEntity() { ... }
    
    public static EconomicIndicatorJpaEntity fromDomainEntity(EconomicIndicator indicator) { ... }
}
```

## 6. リポジトリパターン

### 6.1 ドメインリポジトリインターフェース
```java
// ドメイン層
public interface EconomicIndicatorRepository {
    EconomicIndicator findById(Long id);
    List<EconomicIndicator> findByCountry(String country);
    EconomicIndicator save(EconomicIndicator indicator);
    void delete(Long id);
    // 他のメソッド...
}
```

### 6.2 リポジトリ実装
```java
// インフラストラクチャ層
@Repository
public class EconomicIndicatorRepositoryImpl implements EconomicIndicatorRepository {
    private final EconomicIndicatorJpaRepository jpaRepository;
    
    @Override
    public EconomicIndicator findById(Long id) {
        return jpaRepository.findById(id)
                .map(EconomicIndicatorJpaEntity::toDomainEntity)
                .orElse(null);
    }
    
    @Override
    public EconomicIndicator save(EconomicIndicator indicator) {
        EconomicIndicatorJpaEntity entity = EconomicIndicatorJpaEntity.fromDomainEntity(indicator);
        entity = jpaRepository.save(entity);
        return entity.toDomainEntity();
    }
    
    // 他のメソッド実装...
}
```

## 7. APIインターフェース

### 7.1 REST API構造
```
/api/v1/indicators             # 経済指標エンドポイント
/api/v1/volatilities           # ボラティリティデータエンドポイント
/api/v1/statistics             # 統計情報エンドポイント
/api/v1/users                  # ユーザー管理エンドポイント
/api/v1/auth                   # 認証エンドポイント
```

### 7.2 バージョニング戦略
- URLパスベースのバージョニング: `/api/v1/indicators`
- 将来のバージョン移行に備えたマッピング機構の実装

### 7.3 レスポンス形式の標準化
```java
public class ApiResponse<T> {
    private String status;     // "success" または "error"
    private T data;            // レスポンスデータ
    private String message;    // 操作メッセージまたはエラー説明
    private LocalDateTime timestamp;
    
    // コンストラクタ、ゲッター、セッター...
    
    public static <T> ApiResponse<T> success(T data) {
        return new ApiResponse<>("success", data, "操作が成功しました", LocalDateTime.now());
    }
    
    public static <T> ApiResponse<T> error(String message) {
        return new ApiResponse<>("error", null, message, LocalDateTime.now());
    }
}
```

## 8. サービス層設計

### 8.1 アプリケーションサービス
```java
@Service
public class EconomicIndicatorService {
    private final EconomicIndicatorRepository repository;
    
    @Transactional(readOnly = true)
    public EconomicIndicatorDTO findById(Long id) {
        EconomicIndicator indicator = repository.findById(id);
        if (indicator == null) {
            throw new ResourceNotFoundException("EconomicIndicator", "id", id);
        }
        return mapToDTO(indicator);
    }
    
    @Transactional
    public EconomicIndicatorDTO create(EconomicIndicatorCreateDTO dto) {
        // バリデーション
        validateIndicatorData(dto);
        
        // マッピングとビジネスロジック
        EconomicIndicator indicator = mapFromDTO(dto);
        
        // 永続化
        indicator = repository.save(indicator);
        
        // 応答用DTOへのマッピング
        return mapToDTO(indicator);
    }
    
    // 他のメソッド...
}
```

### 8.2 ドメインサービス
```java
@Service
public class VolatilityCalculationService {
    // ドメイン内の複雑なビジネスロジック
    public List<VolatilityData> calculateHistoricalVolatility(List<MarketData> marketDataList, TimeFrame timeFrame) {
        // 複雑な計算ロジック
        // このロジックはドメインの知識に依存し、技術的な詳細とは無関係
        return calculatedData;
    }
    
    public Map<VolatilityCategory, Double> categorizeVolatility(List<Double> volatilityValues) {
        // 大・中・小の3分類アルゴリズム
        return categorizedValues;
    }
}
```

## 9. エラーハンドリング

### 9.1 例外階層
```
Exception
 └─ RuntimeException
     └─ ApplicationException
         ├─ ResourceNotFoundException
         ├─ ValidationException
         ├─ BusinessRuleViolationException
         └─ ExternalServiceException
```

### 9.2 集中例外ハンドラー
```java
@ControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ApiResponse<Void>> handleResourceNotFoundException(ResourceNotFoundException ex) {
        ApiResponse<Void> response = ApiResponse.error(ex.getMessage());
        return new ResponseEntity<>(response, HttpStatus.NOT_FOUND);
    }
    
    @ExceptionHandler(ValidationException.class)
    public ResponseEntity<ApiResponse<Map<String, String>>> handleValidationException(ValidationException ex) {
        ApiResponse<Map<String, String>> response = ApiResponse.error("入力検証エラー");
        response.setData(ex.getErrors());
        return new ResponseEntity<>(response, HttpStatus.BAD_REQUEST);
    }
    
    // 他の例外ハンドラー...
}
```

## 10. パフォーマンスと最適化

### 10.1 データベースアクセス最適化
- インデックス戦略
- 効率的なJPQLクエリの使用
- N+1問題の回避
- 適切なフェッチ戦略の選択

### 10.2 キャッシュ戦略
```java
@Configuration
@EnableCaching
public class CachingConfig {
    @Bean
    public CacheManager cacheManager() {
        CaffeineCacheManager cacheManager = new CaffeineCacheManager(
            "indicators", "volatilityStatistics", "userSettings");
        
        cacheManager.setCaffeine(Caffeine.newBuilder()
            .expireAfterWrite(30, TimeUnit.MINUTES)
            .maximumSize(1000));
        
        return cacheManager;
    }
}
```

### 10.3 非同期処理
```java
@Configuration
@EnableAsync
public class AsyncConfig {
    @Bean
    public Executor asyncExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(10);
        executor.setQueueCapacity(25);
        executor.setThreadNamePrefix("AsyncTask-");
        executor.initialize();
        return executor;
    }
}
```

## 11. セキュリティ設計

### 11.1 認証・認可
```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf().disable()
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/v1/auth/**").permitAll()
                .requestMatchers(HttpMethod.GET, "/api/v1/indicators/**").permitAll()
                .anyRequest().authenticated())
            .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            .and()
            .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);
        
        return http.build();
    }
    
    // 他のセキュリティ設定...
}
```

### 11.2 JWT設定
```java
@Component
public class JwtTokenProvider {
    @Value("${app.jwt.secret}")
    private String jwtSecret;
    
    @Value("${app.jwt.expiration}")
    private int jwtExpiration;
    
    public String generateToken(Authentication authentication) { ... }
    public String getUsernameFromToken(String token) { ... }
    public boolean validateToken(String token) { ... }
}
```

## 12. CI/CD パイプライン

### 12.1 GitHub Actions設定
```yaml
name: Java CI with Maven

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up JDK 17
      uses: actions/setup-java@v3
      with:
        java-version: '17'
        distribution: 'temurin'
    - name: Build with Maven
      run: mvn -B package --file pom.xml
    - name: Run tests
      run: mvn test
    - name: Code quality analysis
      run: mvn sonar:sonar
  
  deploy-dev:
    needs: build
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Deploy to Dev
      run: ./deploy-dev.sh
      
  deploy-prod:
    needs: build
    if: github.ref == 'refs/heads/main'
    environment: production
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Deploy to Production
      run: ./deploy-prod.sh
``` 