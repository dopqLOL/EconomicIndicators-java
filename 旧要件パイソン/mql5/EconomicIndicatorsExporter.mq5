//+------------------------------------------------------------------+
//|                                 EconomicIndicatorsExporter.mq5 |
//|                        Copyright 2024, Your Name/Company |
//|                                             https://www.example.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, Your Name/Company"
#property link      "https://www.example.com"
#property version   "1.00"
#property script_show_inputs

//--- 入力パラメータ
input datetime InpDateStart = D'2025.05.01';     // 取得開始日
input datetime InpDateEnd   = D'2025.05.18';     // 取得終了日 (0 = 現在日時)
// input string   InpCountries = "US,JP,EUR,GB";   // 対象国コード (カンマ区切り、例: "US,JP,EUR") // この行をコメントアウトまたは削除
                                             // 主要国コード例: US(アメリカ), JP(日本), EU(ユーロ圏全体), DE(ドイツ), FR(フランス), GB(イギリス), CA(カナダ), AU(オーストラリア), NZ(ニュージーランド), CH(スイス), CN(中国)

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
//| スクリプトプログラムスタート関数                                        |
//+------------------------------------------------------------------+
void OnStart()
  {
//--- 取得終了日が0の場合は現在日時を設定
   datetime dateEnd = InpDateEnd;
   if(dateEnd == 0)
      dateEnd = TimeCurrent();

//--- ファイル名の生成
   string startDateStr = TimeToString(InpDateStart, TIME_DATE);
   string endDateStr   = TimeToString(dateEnd, TIME_DATE);
   StringReplace(startDateStr, ".", "");
   StringReplace(endDateStr, ".", "");
   string fileName = "EconomicIndicators_" + startDateStr + "-" + endDateStr + ".csv";

//--- ファイルオープン
   int fileHandle = FileOpen(fileName, FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   if(fileHandle == INVALID_HANDLE)
     {
      PrintFormat("ファイルを開けませんでした: %s, Error: %d", fileName, GetLastError());
      return;
     }
   PrintFormat("ファイルを開きました: %s", fileName);

//--- ヘッダー行の書き込み
   FileWrite(fileHandle, "DateTime (UTC)", "Currency", "EventName", "Forecast", "Actual");

//--- 対象国コードを配列に分割 (このセクション全体を削除またはコメントアウト)
/*
   string countriesArray[];
   ushort u_sep = StringGetCharacter(",", 0);
   StringSplit(InpCountries, u_sep, countriesArray); // InpCountries を使わなくなる
   for(int i = 0; i < ArraySize(countriesArray); i++)
     {
      StringTrimLeft(countriesArray[i]);
      StringTrimRight(countriesArray[i]);
     }
*/

//--- 経済指標の値を取得 (構造を大きく変更)
   MqlCalendarValue values[]; // カレンダー値の配列を直接取得する
   int total_values = 0;

   // 特定の国や通貨でフィルタリングする場合 (入力パラメータ InpCountries を利用)
   // CalendarValueHistory の第4引数は単一国コード(string)、またはNULL。複数国はループで対応
   // または、country_code に NULL を指定して全取得後、手動フィルター

   // if(ArraySize(countriesArray) > 0 && countriesArray[0] != "") // 国フィルターの条件分岐を削除
   //  {
   //   for(int c = 0; c < ArraySize(countriesArray); c++)
   //     {
   //      MqlCalendarValue country_values[];
   //      int num_country_values = CalendarValueHistory(country_values, InpDateStart, dateEnd, countriesArray[c], (string)NULL);
   //      if(num_country_values > 0)
   //        {
   //         int current_total = ArraySize(values);
   //         ArrayResize(values, current_total + num_country_values);
   //         for(int v_idx = 0; v_idx < num_country_values; v_idx++)
   //           {
   //            values[current_total + v_idx] = country_values[v_idx];
   //           }
   //        }
   //      total_values = ArraySize(values);
   //     }
   //  }
   // else // 国指定がない場合 (全件取得) -> これをデフォルトの動作とする
   //  {
      // 注意: 国を指定しない CalendarValueHistory は非常に多くのデータを返す可能性があり、
      // 負荷が高いか、ブローカーにより制限される場合があります。
      total_values = CalendarValueHistory(values, InpDateStart, dateEnd, (string)NULL, (string)NULL);
   //  }

   if(total_values <= 0)
     {
      PrintFormat("指定期間・条件で経済指標データが見つかりませんでした。期間: %s - %s", // InpCountries を削除
                  TimeToString(InpDateStart), TimeToString(dateEnd));
      FileClose(fileHandle);
      return;
     }

   PrintFormat("取得対象イベント数: %d", total_values);

   int eventsProcessed = 0;
   // string eventCurrency; // MqlCalendarValue には直接通貨情報はない。event_detail から取得

//--- 各イベントの詳細情報を取得してファイルに書き込み
   for(int i = 0; i < total_values; i++)
     {
      MqlCalendarEvent event_detail;
      // string currency_str = "DEBUG_CURRENCY"; // デバッグ用コードを元に戻す準備
      string currency_str = ""; // 初期化

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
          country_code_from_info = country_info.id; // "US", "JP" などを期待
      }
      currency_str = GetCurrencyFromCountryID(event_detail.country_id, country_code_from_info);

      if(currency_str == "") { // 通貨が解決できなかった場合
          // PrintFormat("通貨特定できず: event_id=%I64u, country_id=%d, country_code_from_info=\'%s\', event_name=\'%s\'", values[i].event_id, event_detail.country_id, country_code_from_info, name_str);
          if (country_code_from_info != "" && !StringIsDigits(country_code_from_info) && StringLen(country_code_from_info) <= 3) {
             // 国コード文字列が取得できていて、それが数字のみでなく、3文字以下ならそのまま使う (例: EUR, USD)
             currency_str = country_code_from_info;
          } else {
             currency_str = "N/A"; // 不明瞭な場合は N/A
          }
      }
      
      FileWrite(fileHandle, time_str, currency_str, name_str, forecast_str, actual_str);
      eventsProcessed++;
     }

   PrintFormat("処理完了。%d 件のイベントをファイルに書き込みました。", eventsProcessed);

//--- ファイルクローズ
   FileClose(fileHandle);
   // 'time' - undeclared identifier のエラーが TIME_DATE や TIME_SECONDS 定数に関して発生している場合、
   // これらはMQL5の標準組み込み定数であるため、通常は特別なincludeは不要です。
   // もしこのエラーが解消しない場合は、MetaEditorのバージョンやインストール環境に
   // 問題がある可能性も考えられます。MetaEditorの再起動や、
   // MetaTraderプラットフォームのアップデートを確認してみてください。
  }
//+------------------------------------------------------------------+
