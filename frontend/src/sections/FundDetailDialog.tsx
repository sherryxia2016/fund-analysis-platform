import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { FundInfo, FundNav, ProfitStats } from '@/types/fund';
import { TrendingUp, BarChart3, Database } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface FundDetailDialogProps {
  fund: FundInfo | null;
  navData: FundNav[];
  profitStats: ProfitStats | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function FundDetailDialog({ fund, navData, profitStats, open, onOpenChange }: FundDetailDialogProps) {
  if (!fund) return null;

  const chartData = navData.map(d => ({
    date: new Date(d.净值日期).toLocaleDateString('zh-CN'),
    nav: d.单位净值,
    change: d.日增长率
  }));

  const recentData = chartData.slice(-30);
  const threeMonthData = chartData.slice(-90);
  const oneYearData = chartData.slice(-365);

  const calculateReturn = (data: typeof chartData) => {
    if (data.length < 2) return 0;
    const start = data[0].nav;
    const end = data[data.length - 1].nav;
    return ((end - start) / start * 100).toFixed(2);
  };

  // 盈利概率标签样式
  const getProfitProbClass = (prob?: number) => {
    if (prob === undefined) return 'text-gray-600';
    if (prob >= 75) return 'text-green-600 font-bold';
    if (prob >= 50) return 'text-green-600';
    return 'text-red-600';
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <div>
              <span className="text-xl">{fund.基金简称}</span>
              <span className="text-sm text-gray-500 ml-2">{fund.基金代码}</span>
            </div>
            <Badge variant="outline">{fund.基金类型}</Badge>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* 基本信息 */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <Card>
              <CardContent className="pt-4">
                <p className="text-sm text-gray-500">一级板块</p>
                <p className="text-lg font-semibold">{fund.一级板块}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <p className="text-sm text-gray-500">二级板块</p>
                <p className="text-lg font-semibold">{fund.二级板块}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <p className="text-sm text-gray-500">基金规模</p>
                <p className="text-lg font-semibold flex items-center gap-1">
                  <Database className="w-4 h-4 text-gray-400" />
                  {fund.基金规模 !== undefined ? `${fund.基金规模.toFixed(1)}亿` : 'N/A'}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <p className="text-sm text-gray-500">30天盈利概率</p>
                <p className={`text-lg font-semibold ${getProfitProbClass(fund.盈利概率)}`}>
                  {fund.盈利概率 !== undefined ? `${fund.盈利概率}%` : 'N/A'}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <p className="text-sm text-gray-500">平均收益率</p>
                <p className={`text-lg font-semibold ${fund.平均收益率 && fund.平均收益率 >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {fund.平均收益率 !== undefined ? `${fund.平均收益率 > 0 ? '+' : ''}${fund.平均收益率}%` : 'N/A'}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* 回测统计 */}
          {profitStats && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  30天回测统计
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <p className="text-sm text-gray-500">盈利概率</p>
                    <p className={`text-2xl font-bold ${profitStats.盈利概率 >= 75 ? 'text-green-600' : profitStats.盈利概率 >= 50 ? 'text-green-500' : 'text-red-600'}`}>
                      {profitStats.盈利概率}%
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-500">平均收益率</p>
                    <p className={`text-2xl font-bold ${profitStats.平均收益率 >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {profitStats.平均收益率 > 0 ? '+' : ''}{profitStats.平均收益率}%
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-500">最大收益</p>
                    <p className="text-2xl font-bold text-green-600">
                      +{profitStats.最大收益}%
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-500">最大亏损</p>
                    <p className="text-2xl font-bold text-red-600">
                      {profitStats.最大亏损}%
                    </p>
                  </div>
                </div>
                <p className="text-xs text-gray-400 text-center mt-4">
                  基于过去 {profitStats.统计样本数} 个交易日的回测数据
                </p>
              </CardContent>
            </Card>
          )}

          {/* 净值走势 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                净值走势
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="1m">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="1m">近1月 ({calculateReturn(recentData)}%)</TabsTrigger>
                  <TabsTrigger value="3m">近3月 ({calculateReturn(threeMonthData)}%)</TabsTrigger>
                  <TabsTrigger value="1y">近1年 ({calculateReturn(oneYearData)}%)</TabsTrigger>
                </TabsList>
                
                <TabsContent value="1m" className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={recentData}>
                      <defs>
                        <linearGradient id="colorNav1" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" tick={{fontSize: 12}} />
                      <YAxis domain={['auto', 'auto']} tick={{fontSize: 12}} />
                      <Tooltip />
                      <Area type="monotone" dataKey="nav" stroke="#3b82f6" fillOpacity={1} fill="url(#colorNav1)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </TabsContent>
                
                <TabsContent value="3m" className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={threeMonthData}>
                      <defs>
                        <linearGradient id="colorNav3" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" tick={{fontSize: 12}} />
                      <YAxis domain={['auto', 'auto']} tick={{fontSize: 12}} />
                      <Tooltip />
                      <Area type="monotone" dataKey="nav" stroke="#3b82f6" fillOpacity={1} fill="url(#colorNav3)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </TabsContent>
                
                <TabsContent value="1y" className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={oneYearData}>
                      <defs>
                        <linearGradient id="colorNav12" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" tick={{fontSize: 10}} interval={30} />
                      <YAxis domain={['auto', 'auto']} tick={{fontSize: 12}} />
                      <Tooltip />
                      <Area type="monotone" dataKey="nav" stroke="#3b82f6" fillOpacity={1} fill="url(#colorNav12)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  );
}
