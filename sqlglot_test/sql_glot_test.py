from sqlglot import parse_one
sql_create_view = """
CREATE VIEW IF NOT EXISTS USEquityMarketData.TradeOnlyAdjustedMinuteBarIndustryStandard 
AS SELECT TradeDate, BarDateTime, Ticker, ASID, ROUND(PriceAdjFactor * t.FirstTradePrice, 4) as FirstTradePrice, 
ROUND(PriceAdjFactor * t.HighTradePrice, 4) as HighTradePrice, ROUND(PriceAdjFactor * t.LowTradePrice, 4) as LowTradePrice, 
ROUND(PriceAdjFactor * t.LastTradePrice, 4) as LastTradePrice, ROUND(PriceAdjFactor * t.VolumeWeightPrice, 6) as VolumeWeightPrice, 
toUInt64(ROUND(t.Volume / VolumeAdjFactor)) as Volume, TotalTrades, eqGetPriceFactorByTicker(Ticker, BarDateTime) as PriceAdjFactor, 
eqGetVolumeFactorByTicker(Ticker, BarDateTime) as VolumeAdjFactor FROM USEquityMarketData.TradeOnlyMinuteBarIndustryStandard t
"""
# Try parse with dialect="clickhouse"
root_view = parse_one(sql_create_view, read="clickhouse")

# Print the parsed output
print(root_view.__repr__)
