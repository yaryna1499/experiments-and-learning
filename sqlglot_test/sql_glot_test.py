from sqlglot import parse_one, expressions as exp
from typing import Sequence
sql_create_view = """
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
# Try parse with dialect="clickhouse"
root_view = parse_one(sql_create_view, read="clickhouse")
from_exp = root_view.find(exp.From)
from_table = from_exp.find(exp.Table)
print(repr(from_table))

