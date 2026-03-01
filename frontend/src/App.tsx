import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useFundData } from '@/hooks/useFundData';
import { FundList } from '@/sections/FundList';
import { SectorIndices } from '@/sections/SectorIndices';
import { FundDetailDialog } from '@/sections/FundDetailDialog';
import { SectorDetailDialog } from '@/sections/SectorDetailDialog';
import type { FundInfo, TimeRange } from '@/types/fund';
import { TrendingUp, BarChart3, PieChart, Activity, Database, RefreshCw } from 'lucide-react';
import './App.css';

function App() {
  const { 
    fundInfo, 
    fundNavData, 
    sectorIndices, 
    primarySectorIndices, 
    sectorTop5, 
    profitProbability,
    loading, 
    error,
    lastUpdated,
    currentPage,
    setCurrentPage,
    itemsPerPage
  } = useFundData();

  const [selectedFund, setSelectedFund] = useState<FundInfo | null>(null);
  const [fundDialogOpen, setFundDialogOpen] = useState(false);
  
  const [selectedSector, setSelectedSector] = useState<string | null>(null);
  const [selectedSectorLevel, setSelectedSectorLevel] = useState<'一级' | '二级'>('二级');
  const [sectorDialogOpen, setSectorDialogOpen] = useState(false);
  const [selectedTimeRange, setSelectedTimeRange] = useState<TimeRange>('3m');

  const handleFundClick = (fund: FundInfo) => {
    setSelectedFund(fund);
    setFundDialogOpen(true);
  };

  const handleSectorClick = (sector: string, level: '一级' | '二级', timeRange: TimeRange) => {
    setSelectedSector(sector);
    setSelectedSectorLevel(level);
    setSelectedTimeRange(timeRange);
    setSectorDialogOpen(true);
  };

  const handleFundCodeClick = (fundCode: string) => {
    const fund = fundInfo.find(f => f.基金代码 === fundCode);
    if (fund) {
      setSelectedFund(fund);
      setFundDialogOpen(true);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">正在加载基金数据...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-red-600 text-lg">加载失败: {error}</p>
        </div>
      </div>
    );
  }

  // 统计数据
  const stats = {
    totalFunds: fundInfo.length,
    primarySectors: new Set(fundInfo.map(f => f.一级板块)).size,
    secondarySectors: new Set(fundInfo.map(f => f.二级板块)).size,
  };

  // 格式化更新时间
  const formatUpdateTime = (date: Date | null) => {
    if (!date) return '未知';
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-blue-600 p-2 rounded-lg">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">A股场外基金分析平台</h1>
                <p className="text-sm text-gray-500">基于历史数据的智能回测分析</p>
              </div>
            </div>
            <div className="flex gap-4 text-sm items-center">
              <div className="text-center">
                <p className="text-gray-500">基金数量</p>
                <p className="font-semibold text-lg">{stats.totalFunds}</p>
              </div>
              <div className="text-center">
                <p className="text-gray-500">一级板块</p>
                <p className="font-semibold text-lg">{stats.primarySectors}</p>
              </div>
              <div className="text-center">
                <p className="text-gray-500">二级板块</p>
                <p className="font-semibold text-lg">{stats.secondarySectors}</p>
              </div>
              <div className="text-center border-l pl-4">
                <p className="text-gray-500 flex items-center gap-1">
                  <RefreshCw className="w-3 h-3" />
                  数据更新
                </p>
                <p className="font-semibold text-xs text-gray-600">{formatUpdateTime(lastUpdated)}</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Tabs defaultValue="funds" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2 max-w-md mx-auto">
            <TabsTrigger value="funds" className="flex items-center gap-2">
              <Database className="w-4 h-4" />
              基金列表
            </TabsTrigger>
            <TabsTrigger value="sectors" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              板块指数
            </TabsTrigger>
          </TabsList>

          <TabsContent value="funds" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="w-5 h-5" />
                  场外基金列表
                  <Badge variant="secondary">{fundInfo.length}只基金</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-4">
                  展示A股场外基金的每日净值、板块分类及基于历史数据回测的30天盈利概率。
                  点击基金卡片查看详细信息和净值走势。
                  <span className="text-green-600 font-medium"> 盈利概率≥75%的基金将显示为绿色标签。</span>
                </p>
              </CardContent>
            </Card>
            <FundList 
              fundInfo={fundInfo} 
              onFundClick={handleFundClick} 
              currentPage={currentPage}
              setCurrentPage={setCurrentPage}
              itemsPerPage={itemsPerPage}
            />
          </TabsContent>

          <TabsContent value="sectors" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChart className="w-5 h-5" />
                  板块净值指数
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-4">
                  基于基金净值数据计算的一级和二级板块指数，反映各板块的整体表现。
                  可选择不同历史时间范围查看板块走势。点击板块卡片查看该板块的Top 5基金。
                </p>
              </CardContent>
            </Card>
            <SectorIndices 
              sectorIndices={sectorIndices}
              primarySectorIndices={primarySectorIndices}
              onSectorClick={handleSectorClick}
            />
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-8">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <p className="text-center text-sm text-gray-500">
            数据仅供参考，不构成投资建议。投资有风险，入市需谨慎。
          </p>
          <p className="text-center text-xs text-gray-400 mt-1">
            数据每日自动更新 | 回测基于过去3年历史数据
          </p>
        </div>
      </footer>

      {/* Dialogs */}
      <FundDetailDialog
        fund={selectedFund}
        navData={selectedFund ? fundNavData[selectedFund.基金代码] || [] : []}
        profitStats={selectedFund ? profitProbability[selectedFund.基金代码] || null : null}
        open={fundDialogOpen}
        onOpenChange={setFundDialogOpen}
      />

      <SectorDetailDialog
        sector={selectedSector}
        level={selectedSectorLevel}
        timeRange={selectedTimeRange}
        sectorData={selectedSector ? (selectedSectorLevel === '二级' ? sectorIndices[selectedSector] : primarySectorIndices[selectedSector]) || [] : []}
        top5Funds={selectedSector ? (selectedSectorLevel === '二级' ? sectorTop5['二级板块'][selectedSector] : sectorTop5['一级板块'][selectedSector]) || [] : []}
        open={sectorDialogOpen}
        onOpenChange={setSectorDialogOpen}
        onFundClick={handleFundCodeClick}
      />
    </div>
  );
}

export default App;
