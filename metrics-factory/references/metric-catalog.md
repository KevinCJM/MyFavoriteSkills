# MetricsFactory Metric Catalog

- Period metrics: 85
- Rolling metrics: 96
- Relative-history config entries not wired: 20
- Long/short config entries not wired: 6

## Default Period List

`2d, 3d, 5d, 6d, 7d, 10d, 15d, 20d, 25d, 50d, 75d, 5m, 6m, 9m, 12m, 2y, 3y, 5y, mtd, qtd, ytd, max`

## Configured Period Metric Windows

- `2d`, `3d`, `5d`, `6d`, `7d`, `10d`, `15d`, `20d`, `25d`, `30d`, `35d`, `50d`, `70d`, `75d`, `5m`, `6m`, `9m`, `12m`, `2y`.
- Default calculation only uses the intersection of `period_list` and configured windows.
- `30d`, `35d`, and `70d` require explicit `p_list`.

## Rolling Windows

`0, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 15, 19, 20, 22, 25, 26, 30, 35, 60, 99`

- `0`: `OBV`, `PVT`, `TR`.
- Other windows: 93 configured rolling indicators each.

## Period Metrics

`TotalReturn, AnnualizedReturn, AverageDailyReturn, AvgPositiveReturn, AvgNegativeReturn, AvgReturnRatio, TotalPositiveReturn, TotalNegativeReturn, TotalReturnRatio, MedianDailyReturn, Volatility, AnnualizedVolatility, MeanAbsoluteDeviation, ReturnRange, RescaledRange, MaxGain, MaxLoss, MaxDrawDown, MaxDrawDownDays, ReturnDrawDownRatio, DrawDownSlope, UlcerIndex, MartinRatio, SharpeRatio, AnnualizedSharpeRatio, ReturnVolatilityRatio, DownsideVolatility, UpsideVolatility, VolatilitySkew, VolatilityRatio, SortinoRatio, GainConsistency, LossConsistency, WinningRatio, LosingRatio, ReturnSkewness, ReturnKurtosis, VaR-99, VaR-95, VaR-90, VaRSharpe-95, VaRModified-99, VaRModified-95, VaRModified-90, VaRModifiedSharpe-95, CVaR-99, CVaR-95, CVaR-90, CVaRModified-99, CVaRModified-95, CVaRModified-90, CVaRSharpe-95, CVaRModifiedSharpe-95, Percentile-1, Percentile-99, Percentile-5, Percentile-95, Percentile-10, Percentile-90, PercentileWin-95, PercentileLoss-95, PercentileWin-90, PercentileLoss-90, TailRatio-90, TailRatio-95, NewHighRatio, CrossProductRatio-1, CrossProductRatio-5, CrossProductRatio-10, HurstExponent, OmegaRatio, ReturnDistributionIntegral, ReturnSlope, KRatio, SortinoSkewness, NetEquitySlope, EquitySmoothness, VolAvg, VolSlope, VolVolatility, MaxHigh, MinLow, HLDiff, AvgHigh, AvgLow`

## Rolling Metrics

`PriceSigma, CloseMA, CloseMADiff, BollUp-2, BollUpDiff-2, BollDo-2, BollDoDiff-2, BollUpDo-2, BollUp-3, BollUpDiff-3, BollDo-3, BollDoDiff-3, BollUpDo-3, L, H, RSV, KDJ-K-3, KDJ-D-3, KDJ-J-3, KDJ-KD-3, KDJ-KJ-3, KDJ-DJ-3, EMA, EMADiff, VolMA, VolMADiff, RSI, OBV, MAOBV, MAOBVDiff, PVT, MAPVT, MAPVTDiff, MTM, MTMMA-3, MTMMADiff-3, MTMMA-6, MTMMADiff-6, MTMMA-10, MTMMADiff-10, TRIX, MATRIX-3, MATRIXDiff-3, MATRIX-5, MATRIXDiff-5, PSY, MAPSY-3, MAPSYDiff-3, MAPSY-6, MAPSYDiff-6, CCI, CR, MACR-10-5, MACRDiff-10-5, MACR-20-9, MACRDiff-20-9, MACR-40-17, MACRDiff-40-17, MACR-62-28, MACRDiff-62-28, VR, MAVR-3, MAVRDiff-3, MAVR-6, MAVRDiff-6, MAVR-12, MAVRDiff-12, AR, BR, BRARDiff, ARDiff-40, ARDiff-180, BRDiff-400, BRDiff-40, BIAS, MABIAS-5, MABIASDiff-5, MABIAS-10, MABIASDiff-10, TR, PDI, MDI, PDIMDIDiff, ADX-6, ADXR-6-6, ADXRDiff-6-6, ADXR-6-14, ADXRDiff-6-14, DKX, DKXDiff, MADKX-5, MADKXDiff-5, MADKX-10, MADKXDiff-10, MADKX-15, MADKXDiff-15`

## Not Wired By Public Entrypoints

`log_return_relative_metrics_dict`, `long_short_metrics`

Suspicious not-wired keys may be prose/comment string concatenation rather than supported metrics:

` 相对历史收益指标 ReturnZScore_2m`, ` 相对历史风险指标 VolatilityRollingRatio_2m`
