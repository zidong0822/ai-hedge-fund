from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd

# 导入现有的工具函数
from src.tools.akshare_api import (
    get_prices,
    get_financial_metrics,
    get_company_info,
    get_industry_analysis,
    get_enhanced_warren_buffett_analysis,
    get_valuation_metrics,
    get_company_news,
    get_real_time_quotes,
    get_all_industries,
    get_industry_peers
)
from src.tools.api import get_market_cap
from src.data.models import Price, FinancialMetrics, CompanyNews

# 直接导入akshare用于涨停股池
import akshare as ak

from app.backend.models.schemas import (
    StockInfoResponse,
    StockPriceResponse,
    StockFinancialMetricsResponse,
    StockAnalysisResponse,
    IndustryAnalysisResponse,
    StockNewsResponse,
    LimitUpStockResponse,
    StrongStockResponse,
    SubNewStockResponse,
    ExplodeBoardStockResponse,
    FallLimitStockResponse
)


class StockService:
    """股票数据服务类"""
    
    def __init__(self):
        pass
    
    async def get_stock_info(self, ticker: str) -> StockInfoResponse:
        """获取股票基本信息"""
        try:
            # 获取公司基本信息
            company_info = get_company_info(ticker)
            
            # 获取实时报价
            real_time_data = get_real_time_quotes([ticker])
            current_price_data = real_time_data[0] if real_time_data else {}
            
            # 获取估值指标
            valuation_metrics = get_valuation_metrics(ticker)
            
            return StockInfoResponse(
                ticker=ticker,
                name=company_info.get('name', ticker),
                industry=company_info.get('industry'),
                market_cap=company_info.get('market_cap'),
                pe_ratio=valuation_metrics.get('pe_ratio'),
                pb_ratio=valuation_metrics.get('pb_ratio'),
                dividend_yield=valuation_metrics.get('dividend_yield'),
                description=company_info.get('description')
            )
        except Exception as e:
            raise Exception(f"获取股票信息失败: {str(e)}")
    
    async def get_stock_prices(self, ticker: str, start_date: str, end_date: str) -> List[StockPriceResponse]:
        """获取股票价格数据"""
        try:
            prices = get_prices(ticker, start_date, end_date)
            
            return [
                StockPriceResponse(
                    ticker=price.ticker,
                    time=price.time,
                    open=price.open,
                    high=price.high,
                    low=price.low,
                    close=price.close,
                    volume=price.volume
                )
                for price in prices
            ]
        except Exception as e:
            raise Exception(f"获取股票价格数据失败: {str(e)}")
    
    async def get_stock_financial_metrics(self, ticker: str, limit: int = 4) -> List[StockFinancialMetricsResponse]:
        """获取股票财务指标"""
        try:
            end_date = datetime.now().strftime("%Y-%m-%d")
            financial_metrics = get_financial_metrics(ticker, end_date, limit=limit)
            
            return [
                StockFinancialMetricsResponse(
                    ticker=metric.ticker,
                    report_period=metric.report_period,
                    revenue=metric.revenue,
                    net_income=metric.net_income,
                    gross_profit=metric.gross_profit,
                    operating_income=metric.operating_income,
                    total_assets=metric.total_assets,
                    total_debt=metric.total_debt,
                    shareholders_equity=metric.shareholders_equity,
                    return_on_equity=metric.return_on_equity,
                    return_on_assets=metric.return_on_assets,
                    debt_to_equity=metric.debt_to_equity
                )
                for metric in financial_metrics
            ]
        except Exception as e:
            raise Exception(f"获取财务指标失败: {str(e)}")
    
    async def search_stocks(self, keyword: str, limit: int = 10) -> List[StockInfoResponse]:
        """搜索股票（这里简化实现，实际可以接入更完整的搜索API）"""
        try:
            # 这里简化实现，实际项目中可以接入专门的股票搜索API
            # 现在只是尝试直接查询输入的ticker
            if len(keyword) <= 6:  # 假设是股票代码
                try:
                    stock_info = await self.get_stock_info(keyword)
                    return [stock_info]
                except:
                    return []
            
            # 如果不是股票代码，返回空结果
            # 实际项目中这里可以接入股票名称搜索API
            return []
        except Exception as e:
            raise Exception(f"搜索股票失败: {str(e)}")
    
    async def get_stock_analysis(self, ticker: str, analysis_type: str = "warren_buffett") -> StockAnalysisResponse:
        """获取股票分析"""
        try:
            if analysis_type == "warren_buffett":
                analysis_data = get_enhanced_warren_buffett_analysis(ticker)
                
                return StockAnalysisResponse(
                    ticker=ticker,
                    analysis_type=analysis_type,
                    score=analysis_data.get('total_score'),
                    recommendation=analysis_data.get('investment_recommendation'),
                    key_metrics=analysis_data.get('key_metrics'),
                    analysis_details=analysis_data.get('detailed_analysis')
                )
            elif analysis_type == "valuation":
                valuation_data = get_valuation_metrics(ticker)
                
                return StockAnalysisResponse(
                    ticker=ticker,
                    analysis_type=analysis_type,
                    key_metrics=valuation_data,
                    analysis_details=valuation_data
                )
            else:
                raise ValueError(f"不支持的分析类型: {analysis_type}")
                
        except Exception as e:
            raise Exception(f"获取股票分析失败: {str(e)}")
    
    async def get_industry_analysis(self, ticker: str) -> IndustryAnalysisResponse:
        """获取行业分析"""
        try:
            industry_data = get_industry_analysis(ticker)
            peers_data = get_industry_peers(ticker)
            
            return IndustryAnalysisResponse(
                industry_name=industry_data.get('industry_name', '未知行业'),
                total_companies=len(peers_data.get('peers', [])),
                average_pe=industry_data.get('industry_avg_pe'),
                average_pb=industry_data.get('industry_avg_pb'),
                top_companies=peers_data.get('peers', [])[:10],
                industry_trends=industry_data.get('industry_trends')
            )
        except Exception as e:
            raise Exception(f"获取行业分析失败: {str(e)}")
    
    async def get_stock_news(self, ticker: str, limit: int = 10) -> List[StockNewsResponse]:
        """获取股票新闻"""
        try:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            news_list = get_company_news(ticker, end_date, start_date, limit)
            
            return [
                StockNewsResponse(
                    ticker=ticker,
                    title=news.title,
                    content=news.content,
                    publish_time=news.published_date,
                    source=news.source,
                    url=news.url
                )
                for news in news_list
            ]
        except Exception as e:
            raise Exception(f"获取股票新闻失败: {str(e)}")
    
    async def get_all_industries_list(self) -> List[Dict[str, Any]]:
        """获取所有行业列表"""
        try:
            return get_all_industries()
        except Exception as e:
            raise Exception(f"获取行业列表失败: {str(e)}")
    
    async def get_real_time_quotes(self, tickers: List[str]) -> List[Dict[str, Any]]:
        """获取实时报价"""
        try:
            return get_real_time_quotes(tickers)
        except Exception as e:
            raise Exception(f"获取实时报价失败: {str(e)}")
    
    async def get_limit_up_pool(self, date: str) -> List[LimitUpStockResponse]:
        """获取涨停股池数据"""
        try:
            # 调用akshare接口获取涨停股池数据
            df = ak.stock_zt_pool_em(date=date)
            
            if df is None or df.empty:
                return []
            
            # 转换为响应模型
            limit_up_stocks = []
            for _, row in df.iterrows():
                # 安全获取数值的辅助函数
                def safe_get(value, default=None, value_type=None):
                    if pd.isna(value) or value in ['--', '', None]:
                        return default
                    if value_type == int:
                        try:
                            return int(float(value))
                        except (ValueError, TypeError):
                            return default
                    elif value_type == float:
                        try:
                            return float(value)
                        except (ValueError, TypeError):
                            return default
                    return str(value) if value is not None else default
                
                stock = LimitUpStockResponse(
                    序号=safe_get(row.get('序号'), 0, int),
                    代码=safe_get(row.get('代码'), ''),
                    名称=safe_get(row.get('名称'), ''),
                    涨跌幅=safe_get(row.get('涨跌幅'), 0.0, float),
                    最新价=safe_get(row.get('最新价'), 0.0, float),
                    成交额=safe_get(row.get('成交额'), 0, int),
                    流通市值=safe_get(row.get('流通市值'), 0.0, float),
                    总市值=safe_get(row.get('总市值'), 0.0, float),
                    换手率=safe_get(row.get('换手率'), 0.0, float),
                    封板资金=safe_get(row.get('封板资金'), 0, int),
                    首次封板时间=safe_get(row.get('首次封板时间')),
                    最后封板时间=safe_get(row.get('最后封板时间')),
                    炸板次数=safe_get(row.get('炸板次数'), 0, int),
                    涨停统计=safe_get(row.get('涨停统计')),
                    连板数=safe_get(row.get('连板数'), 1, int),
                    所属行业=safe_get(row.get('所属行业'))
                )
                limit_up_stocks.append(stock)
            
            return limit_up_stocks
            
        except Exception as e:
            raise Exception(f"获取涨停股池数据失败: {str(e)}")
    
    async def get_strong_stock_pool(self, date: str) -> List[StrongStockResponse]:
        """获取强势股池数据"""
        try:
            # 调用akshare接口获取强势股池数据
            df = ak.stock_zt_pool_strong_em(date=date)
            
            if df is None or df.empty:
                return []
            
            # 转换为响应模型
            strong_stocks = []
            for _, row in df.iterrows():
                # 安全获取数值的辅助函数
                def safe_get(value, default=None, value_type=None):
                    if pd.isna(value) or value in ['--', '', None]:
                        return default
                    if value_type == int:
                        try:
                            return int(float(value))
                        except (ValueError, TypeError):
                            return default
                    elif value_type == float:
                        try:
                            return float(value)
                        except (ValueError, TypeError):
                            return default
                    return str(value) if value is not None else default
                
                stock = StrongStockResponse(
                    序号=safe_get(row.get('序号'), 0, int),
                    代码=safe_get(row.get('代码'), ''),
                    名称=safe_get(row.get('名称'), ''),
                    涨跌幅=safe_get(row.get('涨跌幅'), 0.0, float),
                    最新价=safe_get(row.get('最新价'), 0.0, float),
                    涨停价=safe_get(row.get('涨停价'), 0.0, float),
                    成交额=safe_get(row.get('成交额'), 0, int),
                    流通市值=safe_get(row.get('流通市值'), 0.0, float),
                    总市值=safe_get(row.get('总市值'), 0.0, float),
                    换手率=safe_get(row.get('换手率'), 0.0, float),
                    涨速=safe_get(row.get('涨速'), 0.0, float),
                    是否新高=safe_get(row.get('是否新高')),
                    量比=safe_get(row.get('量比'), 0.0, float),
                    涨停统计=safe_get(row.get('涨停统计')),
                    入选理由=safe_get(row.get('入选理由')),
                    所属行业=safe_get(row.get('所属行业'))
                )
                strong_stocks.append(stock)
            
            return strong_stocks
            
        except Exception as e:
            raise Exception(f"获取强势股池数据失败: {str(e)}")
    
    async def get_sub_new_stock_pool(self, date: str) -> List[SubNewStockResponse]:
        """获取次新股池数据"""
        try:
            # 调用akshare接口获取次新股池数据
            df = ak.stock_zt_pool_sub_new_em(date=date)
            
            if df is None or df.empty:
                return []
            
            # 转换为响应模型
            sub_new_stocks = []
            for _, row in df.iterrows():
                # 安全获取数值的辅助函数
                def safe_get(value, default=None, value_type=None):
                    if pd.isna(value) or value in ['--', '', None]:
                        return default
                    if value_type == int:
                        try:
                            return int(float(value))
                        except (ValueError, TypeError):
                            return default
                    elif value_type == float:
                        try:
                            return float(value)
                        except (ValueError, TypeError):
                            return default
                    return str(value) if value is not None else default
                
                stock = SubNewStockResponse(
                    序号=safe_get(row.get('序号'), 0, int),
                    代码=safe_get(row.get('代码'), ''),
                    名称=safe_get(row.get('名称'), ''),
                    涨跌幅=safe_get(row.get('涨跌幅'), 0.0, float),
                    最新价=safe_get(row.get('最新价'), 0.0, float),
                    涨停价=safe_get(row.get('涨停价'), 0.0, float),
                    成交额=safe_get(row.get('成交额'), 0, int),
                    流通市值=safe_get(row.get('流通市值'), 0.0, float),
                    总市值=safe_get(row.get('总市值'), 0.0, float),
                    转手率=safe_get(row.get('转手率'), 0.0, float),
                    开板几日=safe_get(row.get('开板几日'), 0, int),
                    开板日期=safe_get(row.get('开板日期'), 0, int),
                    上市日期=safe_get(row.get('上市日期'), 0, int),
                    是否新高=safe_get(row.get('是否新高'), 0, int),
                    涨停统计=safe_get(row.get('涨停统计')),
                    所属行业=safe_get(row.get('所属行业'))
                )
                sub_new_stocks.append(stock)
            
            return sub_new_stocks
            
        except Exception as e:
            raise Exception(f"获取次新股池数据失败: {str(e)}")
    
    async def get_explode_board_stock_pool(self, date: str) -> List[ExplodeBoardStockResponse]:
        """获取炸板股池数据"""
        try:
            # 调用akshare接口获取炸板股池数据
            df = ak.stock_zt_pool_zbgc_em(date=date)
            
            if df is None or df.empty:
                return []
            
            # 转换为响应模型
            explode_board_stocks = []
            for _, row in df.iterrows():
                # 安全获取数值的辅助函数
                def safe_get(value, default=None, value_type=None):
                    if pd.isna(value) or value in ['--', '', None]:
                        return default
                    if value_type == int:
                        try:
                            return int(float(value))
                        except (ValueError, TypeError):
                            return default
                    elif value_type == float:
                        try:
                            return float(value)
                        except (ValueError, TypeError):
                            return default
                    return str(value) if value is not None else default
                
                stock = ExplodeBoardStockResponse(
                    序号=safe_get(row.get('序号'), 0, int),
                    代码=safe_get(row.get('代码'), ''),
                    名称=safe_get(row.get('名称'), ''),
                    涨跌幅=safe_get(row.get('涨跌幅'), 0.0, float),
                    最新价=safe_get(row.get('最新价'), 0.0, float),
                    涨停价=safe_get(row.get('涨停价'), 0.0, float),
                    成交额=safe_get(row.get('成交额'), 0, int),
                    流通市值=safe_get(row.get('流通市值'), 0.0, float),
                    总市值=safe_get(row.get('总市值'), 0.0, float),
                    换手率=safe_get(row.get('换手率'), 0.0, float),
                    涨速=safe_get(row.get('涨速'), 0, int),
                    首次封板时间=safe_get(row.get('首次封板时间')),
                    炸板次数=safe_get(row.get('炸板次数'), 0, int),
                    涨停统计=safe_get(row.get('涨停统计'), 0, int),
                    振幅=safe_get(row.get('振幅')),
                    所属行业=safe_get(row.get('所属行业'))
                )
                explode_board_stocks.append(stock)
            
            return explode_board_stocks
            
        except Exception as e:
            raise Exception(f"获取炸板股池数据失败: {str(e)}")
    
    async def get_fall_limit_stock_pool(self, date: str) -> List[FallLimitStockResponse]:
        """获取跌停股池数据"""
        try:
            # 调用akshare接口获取跌停股池数据
            df = ak.stock_zt_pool_dtgc_em(date=date)
            
            if df is None or df.empty:
                return []
            
            # 转换为响应模型
            fall_limit_stocks = []
            for _, row in df.iterrows():
                # 安全获取数值的辅助函数
                def safe_get(value, default=None, value_type=None):
                    if pd.isna(value) or value in ['--', '', None]:
                        return default
                    if value_type == int:
                        try:
                            return int(float(value))
                        except (ValueError, TypeError):
                            return default
                    elif value_type == float:
                        try:
                            return float(value)
                        except (ValueError, TypeError):
                            return default
                    return str(value) if value is not None else default
                
                stock = FallLimitStockResponse(
                    序号=safe_get(row.get('序号'), 0, int),
                    代码=safe_get(row.get('代码'), ''),
                    名称=safe_get(row.get('名称'), ''),
                    涨跌幅=safe_get(row.get('涨跌幅'), 0.0, float),
                    最新价=safe_get(row.get('最新价'), 0.0, float),
                    成交额=safe_get(row.get('成交额'), 0, int),
                    流通市值=safe_get(row.get('流通市值'), 0.0, float),
                    总市值=safe_get(row.get('总市值'), 0.0, float),
                    动态市盈率=safe_get(row.get('动态市盈率'), 0.0, float),
                    换手率=safe_get(row.get('换手率'), 0.0, float),
                    封单资金=safe_get(row.get('封单资金'), 0, int),
                    最后封板时间=safe_get(row.get('最后封板时间')),
                    板上成交额=safe_get(row.get('板上成交额'), 0, int),
                    连续跌停=safe_get(row.get('连续跌停'), 0, int),
                    开板次数=safe_get(row.get('开板次数'), 0, int),
                    所属行业=safe_get(row.get('所属行业'))
                )
                fall_limit_stocks.append(stock)
            
            return fall_limit_stocks
            
        except Exception as e:
            raise Exception(f"获取跌停股池数据失败: {str(e)}")


# 创建全局服务实例
stock_service = StockService() 