import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import type { SectorIndex, TimeRange } from '@/types/fund';
import { TrendingUp, TrendingDown, Calendar } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';

interface SectorIndicesProps {
  sectorIndices: Record<string, SectorIndex[]>;
  primarySectorIndices: Record<string, SectorIndex[]>;
  onSectorClick: (sector: string, level: '一级' | '二级', timeRange: TimeRange) => void;
}

const timeRangeMap: Record<TimeRange, number> = {
  '1m': 30,
  '3m': 90,
  '6m': 180,
  '1y': 365,
  '1.5y': 548,
  '2y': 730,
  '3y': 1095,
  'all': Infinity
};

const timeRangeLabels: Record<TimeRange, string> = {
  '1m': '近1月',
  '3m': '近3月',
  '6m': '近6月',
  '1y': '近1年',
  '1.5y': '近1.5年',
  '2y': '近2年',
  '3y': '近3年',
  'all': '全部'
};

export function SectorIndices({ sectorIndices, primarySectorIndices, onSectorClick }: SectorIndicesProps) {
  const [activeTab, setActiveTab] = useState('二级');
  const [timeRange, setTimeRange] = useState<TimeRange>('3m');

  const calculateCumulativeReturn = (data: SectorIndex[]) => {
    if (!data || data.length === 0) return 0;
    let cumulative = 1;
    data.forEach(d => {
      cumulative *= (1 + d.日收益率 / 100);
    });
    return (cumulative - 1) * 100;
  };

  const getSectorStats = (data: SectorIndex[]) => {
    if (!data || data.length === 0) return { return: 0, volatility: 0, positiveDays: 0 };
    
    const returns = calculateCumulativeReturn(data);
    const avgReturn = data.reduce((sum, d) => sum + d.日收益率, 0) / data.length;
    const variance = data.reduce((sum, d) => sum + Math.pow(d.日收益率 - avgReturn, 2), 0) / data.length;
    const volatility = Math.sqrt(variance) * Math.sqrt(252);
    const positiveDays = data.filter(d => d.日收益率 > 0).length / data.length * 100;
    
    return {
      return: returns,
      volatility,
      positiveDays
    };
  };

  const filterDataByTimeRange = (data: SectorIndex[]) => {
    if (!data || data.length === 0) return [];
    const days = timeRangeMap[timeRange];
    if (days === Infinity) return data;
    return data.slice(-days);
  };

  const renderSectorCards = (indices: Record<string, SectorIndex[]>) => {
    return Object.entries(indices).map(([sector, data]) => {
      const filteredData = filterDataByTimeRange(data);
      const stats = getSectorStats(filteredData);
      const chartData = filteredData.slice(-30).map(d => ({
        date: new Date(d.日期).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }),
        return: d.日收益率
      }));

      return (
        <Card 
          key={sector}
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => onSectorClick(sector, activeTab === '二级' ? '二级' : '一级', timeRange)}
        >
          <CardHeader className="pb-2">
            <div className="flex justify-between items-center">
              <CardTitle className="text-base font-semibold">{sector}</CardTitle>
              <Badge variant={stats.return >= 0 ? 'default' : 'destructive'}>
                {stats.return >= 0 ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                {stats.return >= 0 ? '+' : ''}{stats.return.toFixed(2)}%
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-24 mb-3">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <Line 
                    type="monotone" 
                    dataKey="return" 
                    stroke={stats.return >= 0 ? '#22c55e' : '#ef4444'}
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-between text-sm text-gray-600">
              <span>波动率: {stats.volatility.toFixed(1)}%</span>
              <span>上涨: {stats.positiveDays.toFixed(0)}%</span>
            </div>
          </CardContent>
        </Card>
      );
    });
  };

  return (
    <div className="space-y-4">
      {/* 时间范围选择 */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-600">历史数据范围:</span>
            <Select value={timeRange} onValueChange={(v) => setTimeRange(v as TimeRange)}>
              <SelectTrigger className="w-[150px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(Object.keys(timeRangeMap) as TimeRange[]).map(range => (
                  <SelectItem key={range} value={range}>
                    {timeRangeLabels[range]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="二级">二级板块</TabsTrigger>
          <TabsTrigger value="一级">一级板块</TabsTrigger>
        </TabsList>

        <TabsContent value="二级" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {renderSectorCards(sectorIndices)}
          </div>
        </TabsContent>

        <TabsContent value="一级" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {renderSectorCards(primarySectorIndices)}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
