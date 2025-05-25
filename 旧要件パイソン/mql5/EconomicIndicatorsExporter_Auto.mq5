//+------------------------------------------------------------------+
//|                          EconomicIndicatorsExporter_Auto.mq5     |
//|                        Copyright 2024, Your Name/Company         |
//|                                     https://www.example.com      |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, Your Name/Company"
#property link      "https://www.example.com"
#property version   "1.10"
#property script_show_inputs

//--- 入力パラメータ
input datetime InpDateStart = D'2025.05.01';     // 取得開始日
input datetime InpDateEnd   = D'2025.05.18';     // 取得終了日 (0 = 現在日時)
input string   InpOutputDir = "EconomicIndicators"; // 出力ディレクトリ (Data/MQL5/Files/ 以下)
input bool     InpAutoExport = false;           // 自動出力モード (true = 定期的に自動出力)
input int      InpAutoExportInterval = 60;      // 自動出力間隔 (分)

//--- グローバル変数
int g_timer_handle = INVALID_HANDLE;            // タイマーハンドル

//+------------------------------------------------------------------+
//| 文字列が数字のみで構成されているか判定するヘルパー関数                       |
//+------------------------------------------------------------------+
bool StringIsDigits(string str)
{
  if(StringLen(str) == 0)
    return false; // 空文字列は数字ではない
  for(int i=0; i<StringLen(str); i++)
  {
    ushort char_code = StringGetCharacter(str,i);
    if(char_code < '0' || char_code > '9')
      return false;
  }
  return true;
}

//+------------------------------------------------------------------+
//| 国IDから通貨シンボルを取得するヘルパー関数                               |
//+------------------------------------------------------------------+
string GetCurrencyFromCountryID(ulong country_id, string country_code_fallback = "")
{
   switch(country_id)
   {
      // 主要国のIDと通貨のマッピング (IDは実行結果のCSVから類推)
      case 36:  return "AUD"; // Australia
      case 76:  return "BRL"; // Brazil
      case 124: return "CAD"; // Canada
      case 156: return "CNY"; // China
      case 250: return "EUR"; // France (Euro)
      case 276: return "EUR"; // Germany (Euro)
      case 344: return "HKD"; // Hong Kong
      case 356: return "INR"; // India
      case 380: return "EUR"; // Italy (Euro)
      case 392: return "JPY"; // Japan
      case 410: return "KRW"; // South Korea
      case 484: return "MXN"; // Mexico
      case 554: return "NZD"; // New Zealand
      case 578: return "NOK"; // Norway
      case 702: return "SGD"; // Singapore
      case 710: return "ZAR"; // South Africa
      case 724: return "EUR"; // Spain (Euro)
      case 752: return "SEK"; // Sweden
      case 756: return "CHF"; // Switzerland
      case 826: return "GBP"; // United Kingdom
      case 840: return "USD"; // United States
      case 999: return "EUR"; // Euro Area / ECB (Global events for Eurozone)
      case 0:   return "GLB"; // Global / Placeholder for events not tied to a specific country/currency
      // 必要に応じて他の国・地域IDと通貨のマッピングを追加
      default:
         // フォールバックとして与えられた国コード文字列から判定
         if(country_code_fallback != "") {
             if(country_code_fallback == "US") return "USD";
             if(country_code_fallback == "JP") return "JPY";
             if(country_code_fallback == "EU" || country_code_fallback == "DE" || country_code_fallback == "FR" || country_code_fallback == "IT" || country_code_fallback == "ES") return "EUR";
             if(country_code_fallback == "GB") return "GBP";
             if(country_code_fallback == "CN") return "CNY";
             if(country_code_fallback == "CA") return "CAD";
             if(country_code_fallback == "AU") return "AUD";
             if(country_code_fallback == "NZ") return "NZD";
             if(country_code_fallback == "CH") return "CHF";
             // 国コード文字列そのものが通貨シンボルと一致する場合 (例: "EUR")
             if(country_code_fallback == "EUR" || country_code_fallback == "USD" || country_code_fallback == "JPY" || 
                country_code_fallback == "GBP" || country_code_fallback == "AUD" || country_code_fallback == "CAD" ||
                country_code_fallback == "CHF" || country_code_fallback == "NZD" || country_code_fallback == "CNY")
                return country_code_fallback;
         }
         return ""; // それでも不明なら空
   }
}

//+------------------------------------------------------------------+
//| 経済指標データをエクスポートする関数                                     |
//+------------------------------------------------------------------+
bool ExportEconomicIndicators()
{
   // 出力ディレクトリの確認と作成
   string output_path = InpOutputDir;
   if(!FolderCreate(output_path))
   {
      // ディレクトリが既に存在する場合は問題ない
      if(GetLastError() != ERR_DIRECTORY_ALREADY_EXISTS)
      {
         PrintFormat("出力ディレクトリの作成に失敗しました: %s, エラー: %d", output_path, GetLastError());
         return false;
      }
   }

   //--- 取得終了日が0の場合は現在日時を設定
   datetime dateEnd = InpDateEnd;
   if(dateEnd == 0)
      dateEnd = TimeCurrent();

   //--- ファイル名の生成
   string startDateStr = TimeToString(InpDateStart, TIME_DATE);
   string endDateStr   = TimeToString(dateEnd, TIME_DATE);
   StringReplace(startDateStr, ".", "");
   StringReplace(endDateStr, ".", "");
   string fileName = output_path + "\\EconomicIndicators_" + startDateStr + "-" + endDateStr + ".csv";

   //--- ファイルオープン
   int fileHandle = FileOpen(fileName, FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   if(fileHandle == INVALID_HANDLE)
   {
      PrintFormat("ファイルを開けませんでした: %s, エラー: %d", fileName, GetLastError());
      return false;
   }
   PrintFormat("ファイルを開きました: %s", fileName);

   //--- ヘッダー行の書き込み
   FileWrite(fileHandle, "DateTime (UTC)", "Currency", "EventName", "Forecast", "Actual");

   //--- 経済指標の値を取得
   MqlCalendarValue values[];
   int total_values = CalendarValueHistory(values, InpDateStart, dateEnd, (string)NULL, (string)NULL);

   if(total_values <= 0)
   {
      PrintFormat("指定期間・条件で経済指標データが見つかりませんでした。期間: %s - %s",
                  TimeToString(InpDateStart), TimeToString(dateEnd));
      FileClose(fileHandle);
      return false;
   }

   PrintFormat("取得対象イベント数: %d", total_values);

   int eventsProcessed = 0;

   //--- 各イベントの詳細情報を取得してファイルに書き込み
   for(int i = 0; i < total_values; i++)
   {
      MqlCalendarEvent event_detail;
      string currency_str = "";

      if(!CalendarEventById(values[i].event_id, event_detail))
      {
         PrintFormat("イベントID %I64u の詳細情報取得に失敗しました。", values[i].event_id);
         continue;
      }

      string time_str     = TimeToString(values[i].time, TIME_DATE | TIME_SECONDS);
      string name_str     = event_detail.name;
      
      string forecast_str;
      if(values[i].forecast_value == EMPTY_VALUE)
         forecast_str = "";
      else
         forecast_str = DoubleToString(values[i].forecast_value, 8);

      string actual_str;
      if(values[i].actual_value == EMPTY_VALUE)
         actual_str = "";
      else
         actual_str = DoubleToString(values[i].actual_value, 8);

      // 通貨シンボルの取得
      string country_code_from_info = "";
      MqlCalendarCountry country_info;
      if(CalendarCountryById(event_detail.country_id, country_info)) {
          country_code_from_info = country_info.id;
      }
      currency_str = GetCurrencyFromCountryID(event_detail.country_id, country_code_from_info);

      if(currency_str == "") {
          if (country_code_from_info != "" && !StringIsDigits(country_code_from_info) && StringLen(country_code_from_info) <= 3) {
             currency_str = country_code_from_info;
          } else {
             currency_str = "N/A";
          }
      }
      
      FileWrite(fileHandle, time_str, currency_str, name_str, forecast_str, actual_str);
      eventsProcessed++;
   }

   PrintFormat("処理完了。%d 件のイベントをファイルに書き込みました。", eventsProcessed);

   //--- ファイルクローズ
   FileClose(fileHandle);
   
   //--- 完了フラグファイルの作成
   string flagFileName = output_path + "\\EconomicIndicators_" + startDateStr + "-" + endDateStr + ".done";
   int flagFileHandle = FileOpen(flagFileName, FILE_WRITE | FILE_TXT, ',');
   if(flagFileHandle != INVALID_HANDLE)
   {
      FileWrite(flagFileHandle, "Export completed at " + TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS));
      FileClose(flagFileHandle);
      PrintFormat("完了フラグファイルを作成しました: %s", flagFileName);
   }
   
   return true;
}

//+------------------------------------------------------------------+
//| タイマーイベントハンドラ                                             |
//+------------------------------------------------------------------+
void OnTimer()
{
   if(InpAutoExport)
   {
      PrintFormat("自動エクスポートを開始します...");
      ExportEconomicIndicators();
   }
}

//+------------------------------------------------------------------+
//| スクリプト終了時の処理                                              |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(g_timer_handle != INVALID_HANDLE)
   {
      EventKillTimer();
      g_timer_handle = INVALID_HANDLE;
   }
}

//+------------------------------------------------------------------+
//| スクリプトプログラムスタート関数                                      |
//+------------------------------------------------------------------+
void OnStart()
{
   // 単発実行モード
   if(!InpAutoExport)
   {
      ExportEconomicIndicators();
      return;
   }
   
   // 自動実行モード
   PrintFormat("自動出力モードを開始します。間隔: %d分", InpAutoExportInterval);
   
   // 即時実行
   ExportEconomicIndicators();
   
   // タイマーの設定
   if(g_timer_handle == INVALID_HANDLE)
   {
      g_timer_handle = EventSetTimer(InpAutoExportInterval * 60); // 秒単位に変換
      if(g_timer_handle == INVALID_HANDLE)
      {
         PrintFormat("タイマーの設定に失敗しました。エラー: %d", GetLastError());
         return;
      }
   }
   
   PrintFormat("タイマーを設定しました。スクリプトを停止するまで %d 分ごとにエクスポートを実行します。", InpAutoExportInterval);
}
//+------------------------------------------------------------------+ 