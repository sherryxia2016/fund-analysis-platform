export interface FundInfo {
  基金代码: string;
  基金简称: string;
  基金类型: string;
  一级板块: string;
  二级板块: string;
  盈利概率?: number;
  平均收益率?: number;
  基金规模?: number;
}

export interface FundNav {
  净值日期: string;
  单位净值: number;
  日增长率: number;
}

export interface SectorIndex {
  日期: string;
  日收益率: number;
  参与基金数: number;
}

export interface ProfitStats {
  盈利概率: number;
  平均收益率: number;
  最大亏损: number;
  最大收益: number;
  统计样本数: number;
}

export interface SectorTop5Item {
  基金代码: string;
  基金简称: string;
  基金类型: string;
  盈利概率: number;
  平均收益率: number;
  基金规模?: number;
}

export type SortOption = 'default' | 'profitDesc' | 'profitAsc' | 'sizeDesc' | 'sizeAsc';

export type TimeRange = '1m' | '3m' | '6m' | '1y' | '1.5y' | '2y' | '3y' | 'all';
