import { useState, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import type { FundInfo, SortOption } from '@/types/fund';
import { Search, TrendingUp, TrendingDown, ArrowUpDown, Database, ChevronLeft, ChevronRight } from 'lucide-react';

interface FundListProps {
  fundInfo: FundInfo[];
  onFundClick: (fund: FundInfo) => void;
  currentPage: number;
  setCurrentPage: (page: number) => void;
  itemsPerPage: number;
}

export function FundList({ fundInfo, onFundClick, currentPage, setCurrentPage, itemsPerPage }: FundListProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSector, setSelectedSector] = useState<string | null>(null);
  const [sortOption, setSortOption] = useState<SortOption>('default');
  const [sizeRange, setSizeRange] = useState<[number, number]>([0, 200]);

  const sectors = useMemo(() => {
    const uniqueSectors = new Set(fundInfo.map(f => f.二级板块));
    return Array.from(uniqueSectors).sort();
  }, [fundInfo]);

  // 计算规模范围
  const sizeStats = useMemo(() => {
    const sizes = fundInfo.map(f => f.基金规模).filter((s): s is number => s !== undefined);
    if (sizes.length === 0) return { min: 0, max: 200 };
    return {
      min: Math.floor(Math.min(...sizes)),
      max: Math.ceil(Math.max(...sizes))
    };
  }, [fundInfo]);

  const filteredFunds = useMemo(() => {
    let filtered = fundInfo.filter(fund => {
      const matchesSearch = fund.基金简称.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          fund.基金代码.includes(searchTerm);
      const matchesSector = selectedSector ? fund.二级板块 === selectedSector : true;
      const matchesSize = fund.基金规模 !== undefined && 
                         fund.基金规模 >= sizeRange[0] && 
                         fund.基金规模 <= sizeRange[1];
      return matchesSearch && matchesSector && matchesSize;
    });

    // 排序
    switch (sortOption) {
      case 'profitDesc':
        filtered = filtered.sort((a, b) => (b.盈利概率 || 0) - (a.盈利概率 || 0));
        break;
      case 'profitAsc':
        filtered = filtered.sort((a, b) => (a.盈利概率 || 0) - (b.盈利概率 || 0));
        break;
      case 'sizeDesc':
        filtered = filtered.sort((a, b) => (b.基金规模 || 0) - (a.基金规模 || 0));
        break;
      case 'sizeAsc':
        filtered = filtered.sort((a, b) => (a.基金规模 || 0) - (b.基金规模 || 0));
        break;
      default:
        // 默认排序（按代码）
        break;
    }

    return filtered;
  }, [fundInfo, searchTerm, selectedSector, sortOption, sizeRange]);

  // 分页逻辑
  const totalPages = Math.ceil(filteredFunds.length / itemsPerPage);
  const paginatedFunds = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return filteredFunds.slice(startIndex, endIndex);
  }, [filteredFunds, currentPage, itemsPerPage]);


  const getProfitBadge = (prob?: number) => {
    if (prob === undefined) return 'secondary';
    if (prob >= 75) return 'default'; // 75%以上用默认（绿色）
    if (prob >= 45) return 'secondary';
    return 'destructive';
  };

  const getProfitBadgeClass = (prob?: number) => {
    if (prob === undefined) return '';
    if (prob >= 75) return 'bg-green-500 hover:bg-green-600 text-white';
    return '';
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="w-5 h-5" />
            基金筛选与排序
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 搜索框 */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="搜索基金名称或代码..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* 排序选项 */}
          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-4 h-4 text-gray-500" />
            <Select value={sortOption} onValueChange={(v) => setSortOption(v as SortOption)}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="排序方式" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="default">默认排序</SelectItem>
                <SelectItem value="profitDesc">盈利概率 ↓ 高到低</SelectItem>
                <SelectItem value="profitAsc">盈利概率 ↑ 低到高</SelectItem>
                <SelectItem value="sizeDesc">基金规模 ↓ 大到小</SelectItem>
                <SelectItem value="sizeAsc">基金规模 ↑ 小到大</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          {/* 板块筛选 */}
          <div className="flex flex-wrap gap-2">
            <Badge 
              variant={selectedSector === null ? 'default' : 'secondary'}
              className="cursor-pointer"
              onClick={() => setSelectedSector(null)}
            >
              全部板块
            </Badge>
            {sectors.map(sector => (
              <Badge
                key={sector}
                variant={selectedSector === sector ? 'default' : 'secondary'}
                className="cursor-pointer"
                onClick={() => setSelectedSector(sector)}
              >
                {sector}
              </Badge>
            ))}
          </div>

          {/* 规模筛选 */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-600">基金规模筛选:</span>
              <span className="text-sm font-medium">{sizeRange[0]}亿 - {sizeRange[1]}亿</span>
            </div>
            <Slider
              value={sizeRange}
              onValueChange={(v) => setSizeRange(v as [number, number])}
              min={sizeStats.min}
              max={sizeStats.max}
              step={5}
              className="w-full"
            />
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {paginatedFunds.map((fund) => (
          <Card 
            key={fund.基金代码}
            className="cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => onFundClick(fund)}
          >
            <CardHeader className="pb-2">
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-base font-semibold line-clamp-1">
                    {fund.基金简称}
                  </CardTitle>
                  <p className="text-sm text-gray-500">{fund.基金代码}</p>
                </div>
                <Badge variant="outline">{fund.基金类型}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-gray-600">{fund.二级板块}</span>
                {fund.基金规模 !== undefined && (
                  <Badge variant="outline" className="text-xs">
                    <Database className="w-3 h-3 mr-1" />
                    {fund.基金规模.toFixed(1)}亿
                  </Badge>
                )}
              </div>
              <div className="flex justify-between items-center">
                {fund.盈利概率 !== undefined && (
                  <Badge 
                    variant={getProfitBadge(fund.盈利概率)}
                    className={getProfitBadgeClass(fund.盈利概率)}
                  >
                    {fund.盈利概率 >= 50 ? (
                      <TrendingUp className="w-3 h-3 mr-1" />
                    ) : (
                      <TrendingDown className="w-3 h-3 mr-1" />
                    )}
                    盈利概率 {fund.盈利概率}%
                  </Badge>
                )}
                {fund.平均收益率 !== undefined && (
                  <span className={`text-sm ${fund.平均收益率 >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {fund.平均收益率 > 0 ? '+' : ''}{fund.平均收益率}%
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredFunds.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          未找到匹配的基金
        </div>
      )}

      {/* 分页组件 */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center space-x-4 py-4">
          <Button 
            variant="outline" 
            size="icon" 
            onClick={() => setCurrentPage(currentPage - 1)} 
            disabled={currentPage === 1}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-sm">
            第 {currentPage} 页 / 共 {totalPages} 页
          </span>
          <Button 
            variant="outline" 
            size="icon" 
            onClick={() => setCurrentPage(currentPage + 1)} 
            disabled={currentPage === totalPages}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
