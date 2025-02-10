
import { useState, useEffect, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useQuery } from "@tanstack/react-query";

interface PivotPoints {
  pivot: number;
  r1: number;
  r2: number;
  r3: number;
  r4: number;
  r5: number;
  s1: number;
  s2: number;
  s3: number;
  s4: number;
  s5: number;
}

interface WatchlistItem {
  symbol: string;
  name: string;
}

interface TimeframeData {
  high: number;
  low: number;
  close: number;
  pivots: PivotPoints | null;
  reached: {
    [key: string]: boolean;
  };
}

const defaultWatchlist: WatchlistItem[] = [
  { symbol: "AAPL", name: "Apple Inc." },
  { symbol: "MSFT", name: "Microsoft Corp." },
  { symbol: "GOOGL", name: "Alphabet Inc." },
  { symbol: "AMZN", name: "Amazon.com" },
  { symbol: "META", name: "Meta Platforms" },
];

const timeframes = [
  { id: "1d", label: "Daily" },
  { id: "1wk", label: "Weekly" },
  { id: "1mo", label: "Monthly" },
  { id: "3mo", label: "Quarterly" },
  { id: "6mo", label: "Semi-Annual" },
  { id: "1y", label: "Yearly" }
];

const PivotCalculator = () => {
  const [selectedSymbol, setSelectedSymbol] = useState<string>("AAPL");
  const [watchlist] = useState<WatchlistItem[]>(defaultWatchlist);
  const [timeframeData, setTimeframeData] = useState<{ [key: string]: TimeframeData }>({});

  const calculatePivots = useCallback((high: number, low: number, close: number): PivotPoints => {
    const pivot = (high + low + close) / 3;
    const r1 = (2 * pivot) - low;
    const s1 = (2 * pivot) - high;
    const r2 = pivot + (high - low);
    const s2 = pivot - (high - low);
    const r3 = high + 2 * (pivot - low);
    const s3 = low - 2 * (high - pivot);
    const r4 = r3 + (r3 - r2);
    const s4 = s3 - (s2 - s3);
    const r5 = r4 + (r4 - r3);
    const s5 = s4 - (s3 - s4);

    return { pivot, r1, r2, r3, r4, r5, s1, s2, s3, s4, s5 };
  }, []);

  const fetchStockData = async (symbol: string) => {
    try {
      const response = await fetch(`https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?interval=1d&range=1y`);
      const data = await response.json();
      
      if (!data.chart || !data.chart.result || !data.chart.result[0]) {
        throw new Error("Invalid data format");
      }

      const quotes = data.chart.result[0].indicators.quote[0];
      const timestamps = data.chart.result[0].timestamp;

      return timeframes.reduce((acc, timeframe) => {
        // Calculate the starting index based on timeframe
        const periodStart = new Date();
        switch (timeframe.id) {
          case "1d": periodStart.setDate(periodStart.getDate() - 1); break;
          case "1wk": periodStart.setDate(periodStart.getDate() - 7); break;
          case "1mo": periodStart.setMonth(periodStart.getMonth() - 1); break;
          case "3mo": periodStart.setMonth(periodStart.getMonth() - 3); break;
          case "6mo": periodStart.setMonth(periodStart.getMonth() - 6); break;
          case "1y": periodStart.setFullYear(periodStart.getFullYear() - 1); break;
        }

        const periodData = timestamps.reduce((period: any, timestamp: number, index: number) => {
          if (new Date(timestamp * 1000) >= periodStart) {
            if (!period.high || quotes.high[index] > period.high) period.high = quotes.high[index];
            if (!period.low || quotes.low[index] < period.low) period.low = quotes.low[index];
            period.close = quotes.close[index]; // Last close
          }
          return period;
        }, { high: 0, low: Infinity, close: 0 });

        const pivots = calculatePivots(periodData.high, periodData.low, periodData.close);
        const currentPrice = quotes.close[quotes.close.length - 1];

        acc[timeframe.id] = {
          ...periodData,
          pivots,
          reached: {
            r5: currentPrice >= pivots.r5,
            r4: currentPrice >= pivots.r4,
            r3: currentPrice >= pivots.r3,
            r2: currentPrice >= pivots.r2,
            r1: currentPrice >= pivots.r1,
            s1: currentPrice <= pivots.s1,
            s2: currentPrice <= pivots.s2,
            s3: currentPrice <= pivots.s3,
            s4: currentPrice <= pivots.s4,
            s5: currentPrice <= pivots.s5,
          }
        };
        return acc;
      }, {});
    } catch (error) {
      console.error("Error fetching data:", error);
      return {};
    }
  };

  const { data: stockData } = useQuery({
    queryKey: ['stockData', selectedSymbol],
    queryFn: () => fetchStockData(selectedSymbol),
    refetchInterval: 300000, // Refetch every 5 minutes
  });

  useEffect(() => {
    if (stockData) {
      setTimeframeData(stockData);
    }
  }, [stockData]);

  const PivotRow = ({ label, value, reached }: { label: string; value: number; reached?: boolean }) => (
    <div 
      className={cn(
        "flex justify-between items-center py-3 px-4 rounded-lg transition-colors",
        reached !== undefined && (reached 
          ? "bg-green-500/20 text-green-700"
          : "bg-red-500/20 text-red-700"
        ),
        !reached && "hover:bg-accent/50"
      )}
    >
      <span className="font-medium text-sm">{label}</span>
      <span className="font-mono text-sm">{value.toFixed(2)}</span>
    </div>
  );

  const TradingViewWidget = ({ symbol }: { symbol: string }) => (
    <div className="w-full h-[500px] rounded-lg overflow-hidden">
      <iframe
        key={symbol}
        src={`https://www.tradingview.com/chart/?symbol=${symbol}&interval=D`}
        style={{ width: "100%", height: "100%", border: "none" }}
      />
    </div>
  );

  return (
    <div className="min-h-screen flex bg-gradient-to-b from-background to-accent/20">
      {/* Watchlist Sidebar */}
      <div className="w-64 border-r bg-card/50 backdrop-blur-sm p-4">
        <div className="font-semibold mb-4">Watchlist</div>
        <ScrollArea className="h-[calc(100vh-8rem)]">
          {watchlist.map((item) => (
            <button
              key={item.symbol}
              onClick={() => setSelectedSymbol(item.symbol)}
              className={cn(
                "w-full text-left px-4 py-3 rounded-lg transition-colors",
                "hover:bg-accent/50",
                selectedSymbol === item.symbol ? "bg-primary/10 text-primary" : ""
              )}
            >
              <div className="font-medium">{item.symbol}</div>
              <div className="text-sm text-muted-foreground">{item.name}</div>
            </button>
          ))}
        </ScrollArea>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-6 space-y-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold tracking-tight">Pivot Plotter Pro</h1>
          <p className="text-muted-foreground">Calculate and track pivot points with precision</p>
        </div>

        {/* Chart */}
        <Card className="p-4 backdrop-blur-sm bg-card/50">
          <TradingViewWidget symbol={selectedSymbol} />
        </Card>

        {/* Pivot Points Tabs */}
        <Card className="backdrop-blur-sm bg-card/50">
          <Tabs defaultValue="1d">
            <TabsList className="grid grid-cols-6 gap-2 p-2">
              {timeframes.map((tf) => (
                <TabsTrigger key={tf.id} value={tf.id}>
                  {tf.label}
                </TabsTrigger>
              ))}
            </TabsList>
            {timeframes.map((tf) => (
              <TabsContent key={tf.id} value={tf.id}>
                <ScrollArea className="h-[400px] rounded-lg">
                  {timeframeData[tf.id]?.pivots && (
                    <div className="p-1">
                      <div className={cn(
                        "py-2 px-4 mb-2 rounded-lg",
                        "bg-primary/10 text-primary font-medium"
                      )}>
                        Resistance Levels
                      </div>
                      <PivotRow label="R5" value={timeframeData[tf.id].pivots.r5} reached={timeframeData[tf.id].reached.r5} />
                      <PivotRow label="R4" value={timeframeData[tf.id].pivots.r4} reached={timeframeData[tf.id].reached.r4} />
                      <PivotRow label="R3" value={timeframeData[tf.id].pivots.r3} reached={timeframeData[tf.id].reached.r3} />
                      <PivotRow label="R2" value={timeframeData[tf.id].pivots.r2} reached={timeframeData[tf.id].reached.r2} />
                      <PivotRow label="R1" value={timeframeData[tf.id].pivots.r1} reached={timeframeData[tf.id].reached.r1} />
                      
                      <div className={cn(
                        "py-2 px-4 my-2 rounded-lg",
                        "bg-accent text-accent-foreground font-medium"
                      )}>
                        Pivot Point: {timeframeData[tf.id].pivots.pivot.toFixed(2)}
                      </div>
                      
                      <div className={cn(
                        "py-2 px-4 mb-2 rounded-lg",
                        "bg-primary/10 text-primary font-medium"
                      )}>
                        Support Levels
                      </div>
                      <PivotRow label="S1" value={timeframeData[tf.id].pivots.s1} reached={timeframeData[tf.id].reached.s1} />
                      <PivotRow label="S2" value={timeframeData[tf.id].pivots.s2} reached={timeframeData[tf.id].reached.s2} />
                      <PivotRow label="S3" value={timeframeData[tf.id].pivots.s3} reached={timeframeData[tf.id].reached.s3} />
                      <PivotRow label="S4" value={timeframeData[tf.id].pivots.s4} reached={timeframeData[tf.id].reached.s4} />
                      <PivotRow label="S5" value={timeframeData[tf.id].pivots.s5} reached={timeframeData[tf.id].reached.s5} />
                    </div>
                  )}
                </ScrollArea>
              </TabsContent>
            ))}
          </Tabs>
        </Card>
      </div>
    </div>
  );
};

export default PivotCalculator;
