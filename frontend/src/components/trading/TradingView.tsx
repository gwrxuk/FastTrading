"use client";

import { useEffect, useRef, useState } from "react";
import { createChart, ColorType, IChartApi, ISeriesApi, CandlestickData, Time } from "lightweight-charts";
import clsx from "clsx";

interface TradingViewProps {
  symbol: string;
}

const INTERVALS = ["1m", "5m", "15m", "1H", "4H", "1D"] as const;

export function TradingView({ symbol }: TradingViewProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const [selectedInterval, setSelectedInterval] = useState<string>("15m");
  const [currentPrice, setCurrentPrice] = useState<number>(2256.78);
  const [priceChange, setPriceChange] = useState<number>(2.34);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#9ca3af",
      },
      grid: {
        vertLines: { color: "rgba(42, 42, 58, 0.3)" },
        horzLines: { color: "rgba(42, 42, 58, 0.3)" },
      },
      crosshair: {
        mode: 1,
        vertLine: {
          color: "#00d4ff",
          width: 1,
          style: 2,
          labelBackgroundColor: "#00d4ff",
        },
        horzLine: {
          color: "#00d4ff",
          width: 1,
          style: 2,
          labelBackgroundColor: "#00d4ff",
        },
      },
      rightPriceScale: {
        borderColor: "rgba(42, 42, 58, 0.5)",
        scaleMargins: {
          top: 0.1,
          bottom: 0.1,
        },
      },
      timeScale: {
        borderColor: "rgba(42, 42, 58, 0.5)",
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartRef.current = chart;

    // Create candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: "#00d4aa",
      downColor: "#ff4757",
      borderUpColor: "#00d4aa",
      borderDownColor: "#ff4757",
      wickUpColor: "#00d4aa",
      wickDownColor: "#ff4757",
    });

    candleSeriesRef.current = candleSeries;

    // Generate mock data
    const data = generateMockCandleData(200);
    candleSeries.setData(data);

    // Add volume histogram
    const volumeSeries = chart.addHistogramSeries({
      color: "#00d4aa",
      priceFormat: {
        type: "volume",
      },
      priceScaleId: "",
    });

    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.85,
        bottom: 0,
      },
    });

    const volumeData = data.map((d) => ({
      time: d.time,
      value: Math.random() * 10000000,
      color: d.close >= d.open ? "rgba(0, 212, 170, 0.3)" : "rgba(255, 71, 87, 0.3)",
    }));

    volumeSeries.setData(volumeData);

    // Fit content
    chart.timeScale().fitContent();

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight - 50,
        });
      }
    };

    handleResize();
    window.addEventListener("resize", handleResize);

    // Simulate real-time updates
    const interval = setInterval(() => {
      if (candleSeriesRef.current) {
        const lastCandle = data[data.length - 1];
        const change = (Math.random() - 0.5) * 10;
        const newClose = lastCandle.close + change;
        
        candleSeriesRef.current.update({
          time: lastCandle.time,
          open: lastCandle.open,
          high: Math.max(lastCandle.high, newClose),
          low: Math.min(lastCandle.low, newClose),
          close: newClose,
        });

        setCurrentPrice(newClose);
        setPriceChange(((newClose - 2200) / 2200) * 100);
      }
    }, 1000);

    return () => {
      window.removeEventListener("resize", handleResize);
      clearInterval(interval);
      chart.remove();
    };
  }, [selectedInterval]);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-display font-bold text-xl">{symbol}</span>
              <span className="text-xs text-terminal-muted bg-terminal-elevated px-2 py-0.5 rounded">
                Spot
              </span>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span className="font-mono text-2xl font-bold">
                ${currentPrice.toFixed(2)}
              </span>
              <span
                className={clsx(
                  "text-sm font-mono",
                  priceChange >= 0 ? "text-bull" : "text-bear"
                )}
              >
                {priceChange >= 0 ? "+" : ""}
                {priceChange.toFixed(2)}%
              </span>
            </div>
          </div>
        </div>

        {/* Interval Selector */}
        <div className="flex items-center gap-1 bg-terminal-elevated rounded-lg p-1">
          {INTERVALS.map((interval) => (
            <button
              key={interval}
              onClick={() => setSelectedInterval(interval)}
              className={clsx(
                "px-3 py-1 text-sm font-medium rounded transition-colors",
                selectedInterval === interval
                  ? "bg-accent-primary text-terminal-bg"
                  : "text-terminal-muted hover:text-white"
              )}
            >
              {interval}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div ref={chartContainerRef} className="flex-1" />
    </div>
  );
}

function generateMockCandleData(count: number): CandlestickData<Time>[] {
  const data: CandlestickData<Time>[] = [];
  let basePrice = 2200;
  const now = Math.floor(Date.now() / 1000);
  const interval = 60 * 15; // 15 minutes

  for (let i = count; i > 0; i--) {
    const volatility = basePrice * 0.01;
    const open = basePrice + (Math.random() - 0.5) * volatility;
    const close = open + (Math.random() - 0.5) * volatility * 2;
    const high = Math.max(open, close) + Math.random() * volatility;
    const low = Math.min(open, close) - Math.random() * volatility;

    data.push({
      time: (now - i * interval) as Time,
      open,
      high,
      low,
      close,
    });

    basePrice = close;
  }

  return data;
}

