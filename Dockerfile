# --- ビルドステージ ---
    FROM maven:3.8.5-openjdk-17 AS builder 

    # 作業ディレクトリを設定
    WORKDIR /app
    
    # Mavenの依存関係をキャッシュするためにpom.xmlだけをコピーして依存関係をダウンロード
    COPY pom.xml .
    RUN mvn dependency:go-offline -B
    
    # ソースコードをコピー
    COPY src ./src
    
    # アプリケーションをビルド
    RUN mvn clean package -DskipTests
    
    # --- 実行ステージ ---
    # ここを修正します
    # FROM openjdk:17-jre-slim  <-- この行をコメントアウトまたは削除して、以下に置き換える
    
    FROM eclipse-temurin:17-jre-jammy 
    
    # 作業ディレクトリを設定
    WORKDIR /app
    
    # ビルドステージで作成したJARファイルをコピー
    COPY --from=builder /app/target/*.jar app.jar
    
    # Spring Bootアプリケーションのデフォルトポートを公開
    EXPOSE 8888
    
    # コンテナ起動時に実行するコマンド
    ENTRYPOINT ["java", "-jar", "app.jar"]