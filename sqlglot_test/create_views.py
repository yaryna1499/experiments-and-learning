"""
SQL CREATE VIEW statements as Python docstring variables
"""

market_calendar_view = """
CREATE VIEW IF NOT EXISTS USEquityReferenceData.MarketCalendar
AS WITH toDate('2007-01-01') as start_date, 
         toDate(date_add(year, 1, toStartOfYear(today())))-1 as end_date
SELECT
    *
FROM 
(
    SELECT
        dates.CalendarDate AS CalendarDate,
        if(toDayOfWeek(CalendarDate) in (6,7) 
           or holidays.`Date` <> '1970-01-01'::date, 0, 1) AS IsTradingDate,
        max(dates.CalendarDate) FILTER (WHERE IsTradingDate = 1) 
            OVER (ORDER BY dates.CalendarDate 
                  ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS PreviousTradingDay,
        min(dates.CalendarDate) FILTER (WHERE IsTradingDate = 1) 
            OVER (ORDER BY dates.CalendarDate 
                  ROWS BETWEEN 1 FOLLOWING AND UNBOUNDED FOLLOWING) AS NextTradingDay
    FROM 
        (SELECT arrayJoin(arrayMap(x -> toDate(x), 
                          range(toUInt32(toStartOfDay(start_date-10)), 
                                toUInt32(toStartOfDay(end_date+10)), 
                                24 * 3600))) AS CalendarDate) AS dates
    LEFT JOIN USEquityReferenceData.MarketHolidays holidays 
        ON holidays.`Date` = dates.CalendarDate
)
WHERE 
    CalendarDate >= start_date 
    AND CalendarDate <= end_date
"""

cumulative_price_adjustments_view = """
CREATE VIEW IF NOT EXISTS USEquityReferenceData.CumulativePriceAdjustments
AS WITH cte_daily_agg AS (  -- can have multiple events per ASID per day
    SELECT
        ASID,
        Ticker,
        EffectiveDate,
        arrayProduct(groupArray(AdjustmentFactor)) as AdjustmentFactor
    FROM USEquityReferenceData.BasicAdjustments
    GROUP BY ASID, Ticker, EffectiveDate
),
cte_cumulative_agg AS (
    SELECT
        ASID,
        Ticker,
        EffectiveDate,
        groupArray(AdjustmentFactor)
            OVER (
                PARTITION BY ASID 
                ORDER BY EffectiveDate ASC 
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS ForwardFactorArr,
        groupArray(AdjustmentFactor)
            OVER (
                PARTITION BY ASID 
                ORDER BY EffectiveDate ASC 
                ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING
            ) AS BackwardFactorArr
    FROM cte_daily_agg
)
SELECT
    ASID,
    Ticker,
    EffectiveDate,
    arrayProduct(ForwardFactorArr) AS ForwardFactor,
    arrayProduct(BackwardFactorArr) AS BackwardFactor
FROM cte_cumulative_agg;
"""

cumulative_price_backward_adjustments_base_view = """
SELECT
    ASID,
    any(EffectiveDate) OVER (
        PARTITION BY ASID 
        ORDER BY EffectiveDate ASC
        ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING
    ) as StartDate,
    EffectiveDate - toIntervalDay(1) as EndDate,
    BackwardFactor
FROM USEquityReferenceData.CumulativePriceAdjustments;
"""

cumulative_volume_adjustments_view = """
CREATE VIEW IF NOT EXISTS USEquityReferenceData.CumulativeVolumeAdjustments
AS WITH cte_daily_agg AS (  -- can have multiple events per ASID per day
    SELECT
        ASID,
        Ticker,
        EffectiveDate,
        arrayProduct(groupArray(AdjustmentFactor)) as AdjustmentFactor
    FROM USEquityReferenceData.BasicAdjustments
    WHERE AdjustmentReason IN (
        'BonusSame', 'CapReduct', 'Cons', 'ScriptDiv', 
        'SecSwap', 'Reclass', 'Subdiv'
    )
    GROUP BY ASID, Ticker, EffectiveDate
),
cte_cumulative_agg AS (
    SELECT
        ASID,
        Ticker,
        EffectiveDate,
        groupArray(AdjustmentFactor)
            OVER (
                PARTITION BY ASID 
                ORDER BY EffectiveDate ASC 
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS ForwardFactorArr,
        groupArray(AdjustmentFactor)
            OVER (
                PARTITION BY ASID 
                ORDER BY EffectiveDate ASC 
                ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING
            ) AS BackwardFactorArr
    FROM cte_daily_agg
)
SELECT
    ASID,
    Ticker,
    EffectiveDate,
    arrayProduct(ForwardFactorArr) AS ForwardFactor,
    arrayProduct(BackwardFactorArr) AS BackwardFactor
FROM cte_cumulative_agg;
"""

cumulative_volume_backward_adjustments_base_view = """
CREATE VIEW IF NOT EXISTS USEquityReferenceData.CumulativeVolumeBackwardAdjustmentsBase
AS SELECT
    ASID,
    any(EffectiveDate) OVER (
        PARTITION BY ASID 
        ORDER BY EffectiveDate ASC
        ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING
    ) as StartDate,
    EffectiveDate - toIntervalDay(1) as EndDate,
    BackwardFactor
FROM USEquityReferenceData.CumulativeVolumeAdjustments
"""

trade_only_adjusted_minute_bar_excluding_trf_view = """
CREATE VIEW IF NOT EXISTS USEquityMarketData.TradeOnlyAdjustedMinuteBarExcludingTRF
AS SELECT
    TradeDate,
    BarDateTime,
    Ticker,
    ASID,
    ROUND(PriceAdjFactor * t.FirstTradePrice, 4) as FirstTradePrice,
    ROUND(PriceAdjFactor * t.HighTradePrice, 4) as HighTradePrice,
    ROUND(PriceAdjFactor * t.LowTradePrice, 4) as LowTradePrice,
    ROUND(PriceAdjFactor * t.LastTradePrice, 4) as LastTradePrice,
    ROUND(PriceAdjFactor * t.VolumeWeightPrice, 6) as VolumeWeightPrice,
    toUInt64(ROUND(t.Volume / VolumeAdjFactor)) as Volume,
    TotalTrades,
    eqGetPriceFactorByTicker(Ticker, BarDateTime) as PriceAdjFactor,
    eqGetVolumeFactorByTicker(Ticker, BarDateTime) as VolumeAdjFactor
FROM USEquityMarketData.TradeOnlyMinuteBarExcludingTRF t
"""

standard_adjusted_ohlc_daily_view = """
CREATE VIEW IF NOT EXISTS USEquityMarketData.StandardAdjustedOHLCDaily
AS SELECT
    TradeDate,
    Ticker,
    ASID,
    ROUND(PriceAdjFactor * t.OpenPrice, 4) as OpenPrice,
    ROUND(PriceAdjFactor * t.HighPrice, 4) as HighPrice,
    ROUND(PriceAdjFactor * t.LowPrice, 4) as LowPrice,
    ROUND(PriceAdjFactor * t.ClosePrice, 4) as ClosePrice,
    toUInt64(ROUND(t.MarketHoursVolume / VolumeAdjFactor)) as MarketHoursVolume,
    eqGetPriceFactorByTicker(Ticker, TradeDate) as PriceAdjFactor,
    eqGetVolumeFactorByTicker(Ticker, TradeDate) as VolumeAdjFactor
FROM USEquityMarketData.StandardOHLCDaily t
"""

trade_only_adjusted_view = """
CREATE VIEW IF NOT EXISTS USEquityMarketData.TradeOnlyAdjusted
AS SELECT
    TradeDate,
    EventDateTime,
    EventType,
    Ticker,
    ASID,
    ROUND(PriceAdjFactor * t.Price, 4) as Price,
    toUInt64(ROUND(t.Quantity / VolumeAdjFactor)) as Quantity,
    Exchange,
    ConditionCode,
    eqGetPriceFactorByTicker(Ticker, EventDateTime) as PriceAdjFactor,
    eqGetVolumeFactorByTicker(Ticker, EventDateTime) as VolumeAdjFactor
FROM USEquityMarketData.TradeOnly t
"""

trade_only_adjusted_minute_bar_view = """
CREATE VIEW IF NOT EXISTS USEquityMarketData.TradeOnlyAdjustedMinuteBar
AS SELECT
    TradeDate,
    BarDateTime,
    Ticker,
    ASID,
    ROUND(PriceAdjFactor * t.FirstTradePrice, 4) as FirstTradePrice,
    ROUND(PriceAdjFactor * t.HighTradePrice, 4) as HighTradePrice,
    ROUND(PriceAdjFactor * t.LowTradePrice, 4) as LowTradePrice,
    ROUND(PriceAdjFactor * t.LastTradePrice, 4) as LastTradePrice,
    ROUND(PriceAdjFactor * t.VolumeWeightPrice, 6) as VolumeWeightPrice,
    toUInt64(ROUND(t.Volume / VolumeAdjFactor)) as Volume,
    TotalTrades,
    eqGetPriceFactorByTicker(Ticker, BarDateTime) as PriceAdjFactor,
    eqGetVolumeFactorByTicker(Ticker, BarDateTime) as VolumeAdjFactor
FROM USEquityMarketData.TradeOnlyMinuteBar t
"""

primary_adjusted_ohlc_daily_view = """
CREATE VIEW IF NOT EXISTS USEquityMarketData.PrimaryAdjustedOHLCDaily
AS SELECT
    TradeDate,
    Ticker,
    ASID,
    Name,
    PrimaryExchange,
    ISIN,
    OpenTime,
    ROUND(PriceAdjFactor * t.OpenPrice, 4) as OpenPrice,
    toUInt64(ROUND(t.OpenSize / VolumeAdjFactor)) as OpenSize,
    HighTime,
    ROUND(PriceAdjFactor * t.HighPrice, 4) as HighPrice,
    LowTime,
    ROUND(PriceAdjFactor * t.LowPrice, 4) as LowPrice,
    CloseTime,
    ROUND(PriceAdjFactor * t.ClosePrice, 4) as ClosePrice,
    toUInt64(ROUND(t.CloseSize / VolumeAdjFactor)) as CloseSize,
    toUInt64(ROUND(t.ListedMarketHoursVolume / VolumeAdjFactor)) as ListedMarketHoursVolume,
    ListedMarketHoursTrades,
    toUInt64(ROUND(t.ListedTotalVolume / VolumeAdjFactor)) as ListedTotalVolume,
    ListedTotalTrades,
    toUInt64(ROUND(t.FinraMarketHoursVolume / VolumeAdjFactor)) as FinraMarketHoursVolume,
    FinraMarketHoursTrades,
    toUInt64(ROUND(t.FinraTotalVolume / VolumeAdjFactor)) as FinraTotalVolume,
    FinraTotalTrades,
    ROUND(PriceAdjFactor * t.MarketVWAP, 6) as MarketVWAP,
    ROUND(PriceAdjFactor * t.DailyVWAP, 6) as DailyVWAP,
    eqGetPriceFactorByTicker(Ticker, TradeDate) as PriceAdjFactor,
    eqGetVolumeFactorByTicker(Ticker, TradeDate) as VolumeAdjFactor
FROM USEquityMarketData.PrimaryOHLCDaily t
"""

trade_only_adjusted_minute_bar_industry_standard_view = """
CREATE VIEW IF NOT EXISTS USEquityMarketData.TradeOnlyAdjustedMinuteBarIndustryStandard
AS SELECT
    TradeDate,
    BarDateTime,
    Ticker,
    ASID,
    ROUND(PriceAdjFactor * t.FirstTradePrice, 4) as FirstTradePrice,
    ROUND(PriceAdjFactor * t.HighTradePrice, 4) as HighTradePrice,
    ROUND(PriceAdjFactor * t.LowTradePrice, 4) as LowTradePrice,
    ROUND(PriceAdjFactor * t.LastTradePrice, 4) as LastTradePrice,
    ROUND(PriceAdjFactor * t.VolumeWeightPrice, 6) as VolumeWeightPrice,
    toUInt64(ROUND(t.Volume / VolumeAdjFactor)) as Volume,
    TotalTrades,
    eqGetPriceFactorByTicker(Ticker, BarDateTime) as PriceAdjFactor,
    eqGetVolumeFactorByTicker(Ticker, BarDateTime) as VolumeAdjFactor
FROM USEquityMarketData.TradeOnlyMinuteBarIndustryStandard t
"""

isin_sec_id_lookup_base_view = """
CREATE VIEW IF NOT EXISTS USEquityReferenceData.ISINSecIdLookupBase
AS SELECT
    SecId,
    ISIN,
    toDate(splitByChar(':', ISINStartToEndDate)[1]) as StartDate,
    toDate(splitByChar(':', ISINStartToEndDate)[2]) as EndDate
FROM (
    SELECT * 
    FROM USEquityReferenceData.SecMasterBase 
    WHERE not has(ISIN, '')
)
ARRAY JOIN 
    ISIN as ISIN, 
    ISINStartToEndDate as ISINStartToEndDate
"""

isin_asid_lookup_base_view = """
CREATE VIEW IF NOT EXISTS USEquityReferenceData.ISINASIDLookupBase
AS SELECT
    ASID,
    ISIN,
    toDate(splitByChar(':', ISINStartToEndDate)[1]) as StartDate,
    toDate(splitByChar(':', ISINStartToEndDate)[2]) as EndDate
FROM (
    SELECT * 
    FROM USEquityReferenceData.SecMasterBase 
    WHERE not has(ISIN, '')
)
ARRAY JOIN 
    ISIN as ISIN, 
    ISINStartToEndDate as ISINStartToEndDate
"""

industry_standard_adjusted_ohlc_daily_view = """
CREATE VIEW IF NOT EXISTS USEquityMarketData.IndustryStandardAdjustedOHLCDaily
AS SELECT
    TradeDate,
    Ticker,
    ASID,
    ROUND(PriceAdjFactor * t.OpenPrice, 4) as OpenPrice,
    ROUND(PriceAdjFactor * t.HighPrice, 4) as HighPrice,
    ROUND(PriceAdjFactor * t.LowPrice, 4) as LowPrice,
    ROUND(PriceAdjFactor * t.ClosePrice, 4) as ClosePrice,
    toUInt64(ROUND(t.MarketHoursVolume / VolumeAdjFactor)) as MarketHoursVolume,
    toUInt64(ROUND(t.MarketHoursFinraVolume / VolumeAdjFactor)) as MarketHoursFinraVolume,
    toUInt64(ROUND(t.DailyVolume / VolumeAdjFactor)) as DailyVolume,
    toUInt64(ROUND(t.DailyFinraVolume / VolumeAdjFactor)) as DailyFinraVolume,
    ROUND(PriceAdjFactor * t.MarketHoursVWAP, 6) as MarketHoursVWAP,
    ROUND(PriceAdjFactor * t.DailyVWAP, 6) as DailyVWAP,
    eqGetPriceFactorByTicker(Ticker, TradeDate) as PriceAdjFactor,
    eqGetVolumeFactorByTicker(Ticker, TradeDate) as VolumeAdjFactor
FROM USEquityMarketData.IndustryStandardOHLCDaily t
"""

algoseek_adjusted_ohlc_daily_view = """
CREATE VIEW IF NOT EXISTS USEquityMarketData.AlgoseekAdjustedOHLCDaily
AS SELECT
    TradeDate,
    Ticker,
    ASID,
    ROUND(PriceAdjFactor * t.OpenPrice, 4) as OpenPrice,
    ROUND(PriceAdjFactor * t.HighPrice, 4) as HighPrice,
    ROUND(PriceAdjFactor * t.LowPrice, 4) as LowPrice,
    ROUND(PriceAdjFactor * t.ClosePrice, 4) as ClosePrice,
    toUInt64(ROUND(t.MarketHoursVolume / VolumeAdjFactor)) as MarketHoursVolume,
    toUInt64(ROUND(t.MarketHoursFinraVolume / VolumeAdjFactor)) as MarketHoursFinraVolume,
    toUInt64(ROUND(t.DailyVolume / VolumeAdjFactor)) as DailyVolume,
    toUInt64(ROUND(t.DailyFinraVolume / VolumeAdjFactor)) as DailyFinraVolume,
    ROUND(PriceAdjFactor * t.MarketHoursVWAP, 6) as MarketHoursVWAP,
    ROUND(PriceAdjFactor * t.DailyVWAP, 6) as DailyVWAP,
    eqGetPriceFactorByTicker(Ticker, TradeDate) as PriceAdjFactor,
    eqGetVolumeFactorByTicker(Ticker, TradeDate) as VolumeAdjFactor
FROM USEquityMarketData.AlgoseekOHLCDaily t
"""

# Dictionary mapping view names to SQL strings for easy access
CREATE_VIEW_QUERIES = {
    'MarketCalendar': market_calendar_view,
    'CumulativePriceAdjustments': cumulative_price_adjustments_view,
    'CumulativePriceBackwardAdjustmentsBase': cumulative_price_backward_adjustments_base_view,
    'CumulativeVolumeAdjustments': cumulative_volume_adjustments_view,
    'CumulativeVolumeBackwardAdjustmentsBase': cumulative_volume_backward_adjustments_base_view,
    'TradeOnlyAdjustedMinuteBarExcludingTRF': trade_only_adjusted_minute_bar_excluding_trf_view,
    'StandardAdjustedOHLCDaily': standard_adjusted_ohlc_daily_view,
    'TradeOnlyAdjusted': trade_only_adjusted_view,
    'TradeOnlyAdjustedMinuteBar': trade_only_adjusted_minute_bar_view,
    'PrimaryAdjustedOHLCDaily': primary_adjusted_ohlc_daily_view,
    'TradeOnlyAdjustedMinuteBarIndustryStandard': trade_only_adjusted_minute_bar_industry_standard_view,
    'ISINSecIdLookupBase': isin_sec_id_lookup_base_view,
    'ISINASIDLookupBase': isin_asid_lookup_base_view,
    'IndustryStandardAdjustedOHLCDaily': industry_standard_adjusted_ohlc_daily_view,
    'AlgoseekAdjustedOHLCDaily': algoseek_adjusted_ohlc_daily_view,
}