import { useState, useEffect, type Dispatch, type SetStateAction } from 'react';
import type { FundInfo, FundNav, SectorIndex, ProfitStats, SectorTop5Item } from '@/types/fund';

interface UseFundDataReturn {
  fundInfo: FundInfo[];
  fundNavData: Record<string, FundNav[]>;
  sectorIndices: Record<string, SectorIndex[]>;
  primarySectorIndices: Record<string, SectorIndex[]>;
  sectorTop5: {
    '二级板块': Record<string, SectorTop5Item[]>;
    '一级板块': Record<string, SectorTop5Item[]>;
  };
  profitProbability: Record<string, ProfitStats>;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  currentPage: number;
  setCurrentPage: Dispatch<SetStateAction<number>>;
  itemsPerPage: number;
  setItemsPerPage: Dispatch<SetStateAction<number>>;
}

export function useFundData(): UseFundDataReturn {
  const [fundInfo, setFundInfo] = useState<FundInfo[]>([]);
  const [fundNavData, setFundNavData] = useState<Record<string, FundNav[]>>({});
  const [sectorIndices, setSectorIndices] = useState<Record<string, SectorIndex[]>>({});
  const [primarySectorIndices, setPrimarySectorIndices] = useState<Record<string, SectorIndex[]>>({});
  const [sectorTop5, setSectorTop5] = useState({
    '二级板块': {},
    '一级板块': {}
  });
  const [profitProbability, setProfitProbability] = useState<Record<string, ProfitStats>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // 分页状态
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(50);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        
        // 添加时间戳参数避免缓存
        const timestamp = new Date().getTime();
        
        // 加载基金信息
        const fundInfoRes = await fetch(`/data/fund_info.json?t=${timestamp}`);
        const rawFundInfo: FundInfo[] = await fundInfoRes.json();
        const parsedFundInfo = rawFundInfo.filter(
          fund => fund.盈利概率 != null && fund.平均收益率 != null && fund.基金规模 != null
        );
        setFundInfo(parsedFundInfo);

        // 加载净值数据
        const navRes = await fetch(`/data/fund_nav_data.json?t=${timestamp}`);
        const navData = await navRes.json();
        setFundNavData(navData);

        // 加载板块指数
        const sectorRes = await fetch(`/data/sector_indices.json?t=${timestamp}`);
        const sectorData = await sectorRes.json();
        setSectorIndices(sectorData);

        // 加载一级板块指数
        const primarySectorRes = await fetch(`/data/primary_sector_indices.json?t=${timestamp}`);
        const primarySectorData = await primarySectorRes.json();
        setPrimarySectorIndices(primarySectorData);

        // 加载板块Top5
        const top5Res = await fetch(`/data/sector_top5.json?t=${timestamp}`);
        const top5Data = await top5Res.json();
        setSectorTop5(top5Data);

        // 加载盈利概率
        const probRes = await fetch(`/data/profit_probability.json?t=${timestamp}`);
        const probData = await probRes.json();
        setProfitProbability(probData);

        setLastUpdated(new Date());
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : '加载数据失败');
        setLoading(false);
      }
    }

    loadData();
    
    // return () => clearInterval(interval);
  }, []);

  return {
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
    itemsPerPage,
    setItemsPerPage,
  };
}
