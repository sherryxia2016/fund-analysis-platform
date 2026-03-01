import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import type { SectorIndex, SectorTop5Item, TimeRange } from '@/types/fund';
import { Trophy, BarChart3, Database } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

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

interface SectorDetailDialogProps {
  sector: string | null;
  level: '一级' | '二级';
  timeRange: TimeRange;
  sectorData: SectorIndex[];
  top5Funds: SectorTop5Item[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onFundClick: (fundCode: string) => void;
}

export function SectorDetailDialog({ 
  sector, 
  level, 
  timeRange,
  sectorData, 
  top5Funds, 
  open, 
  onOpenChange,
  onFundClick 
}: SectorDetailDialogProps) {
  if (!sector) return null;

  const filterDataByTimeRange = (data: SectorIndex[]) => {
    if (!data || data.length === 0) return [];
    const days = timeRangeMap[timeRange];
    if (days === Infinity) return data;
    return data.slice(-days);
  };

  const filteredSectorData = filterDataByTimeRange(sectorData);

  const chartData = filteredSectorData.map(d => ({
    date: new Date(d.日期).toLocaleDateString('zh-CN'),
    return: d.日收益率,
    cumulative: 0
  }));

  // 计算累计收益
  let cumulative = 0;
  chartData.forEach(d => {
    cumulative += d.return;
    d.cumulative = cumulative;
  });

  const stats = {
    totalReturn: chartData.length > 0 ? chartData[chartData.length - 1].cumulative : 0,
    avgDailyReturn: filteredSectorData.length > 0 ? filteredSectorData.reduce((sum, d) => sum + d.日收益率, 0) / filteredSectorData.length : 0,
    positiveDays: filteredSectorData.length > 0 ? filteredSectorData.filter(d => d.日收益率 > 0).length / filteredSectorData.length * 100 : 0,
    volatility: filteredSectorData.length > 0 ? Math.sqrt(filteredSectorData.reduce((sum, d) => sum + Math.pow(d.日收益率 - (filteredSectorData.reduce((s, x) => s + x.日收益率, 0) / filteredSectorData.length), 2), 0) / filteredSectorData.length) * Math.sqrt(252) : 0
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xl">{sector}</span>
              <Badge variant="secondary">{level}板块</Badge>
            </div>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* 统计信息 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-4">
                <p className="text-sm text-gray-500">累计收益</p>
                <p className={`text-lg font-semibold ${stats.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {stats.totalReturn >= 0 ? '+' : ''}{stats.totalReturn.toFixed(2)}%
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <p className="text-sm text-gray-500">日均收益</p>
                <p className={`text-lg font-semibold ${stats.avgDailyReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {stats.avgDailyReturn >= 0 ? '+' : ''}{stats.avgDailyReturn.toFixed(3)}%
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <p className="text-sm text-gray-500">上涨天数占比</p>
                <p className="text-lg font-semibold">{stats.positiveDays.toFixed(1)}%</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <p className="text-sm text-gray-500">年化波动率</p>
                <p className="text-lg font-semibold">{stats.volatility.toFixed(2)}%</p>
              </CardContent>
            </Card>
          </div>

          {/* 板块走势 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                板块累计收益走势
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="colorCumulative" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{fontSize: 10}} interval={30} />
                    <YAxis tick={{fontSize: 12}} />
                    <Tooltip />
                    <Area 
                      type="monotone" 
                      dataKey="cumulative" 
                      stroke="#8b5cf6" 
                      fillOpacity={1} 
                      fill="url(#colorCumulative)" 
                      name="累计收益(%)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Top 5 基金 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="w-5 h-5" />
                {sector} - 盈利概率Top 5基金
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>排名</TableHead>
                    <TableHead>基金代码</TableHead>
                    <TableHead>基金名称</TableHead>
                    <TableHead>基金类型</TableHead>
                    <TableHead className="text-right">基金规模</TableHead>
                    <TableHead className="text-right">盈利概率</TableHead>
                    <TableHead className="text-right">平均收益率</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {top5Funds.map((fund, index) => (
                    <TableRow 
                      key={fund.基金代码}
                      className="cursor-pointer hover:bg-gray-50"
                      onClick={() => onFundClick(fund.基金代码)}
                    >
                      <TableCell>
                        <Badge variant={index < 3 ? 'default' : 'secondary'}>
                          {index + 1}
                        </Badge>
                      </TableCell>
                      <TableCell>{fund.基金代码}</TableCell>
                      <TableCell className="font-medium">{fund.基金简称}</TableCell>
                      <TableCell>{fund.基金类型}</TableCell>
                      <TableCell className="text-right">
                        <span className="flex items-center justify-end gap-1">
                          <Database className="w-3 h-3 text-gray-400" />
                          {fund.基金规模 !== undefined ? `${fund.基金规模.toFixed(1)}亿` : 'N/A'}
                        </span>
                      </TableCell>
                      <TableCell className={`text-right font-semibold ${fund.盈利概率 >= 75 ? 'text-green-600 font-bold' : fund.盈利概率 >= 50 ? 'text-green-600' : 'text-red-600'}`}>
                        {fund.盈利概率}%
                      </TableCell>
                      <TableCell className={`text-right ${fund.平均收益率 >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {fund.平均收益率 >= 0 ? '+' : ''}{fund.平均收益率}%
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  );
}
