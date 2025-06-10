import datetime
import pandas as pd
from typing import Optional, List
import akshare as ak

from src.data.cache import get_cache
from src.data.models import (
    CompanyNews,
    CompanyNewsResponse,
    FinancialMetrics,
    FinancialMetricsResponse,
    Price,
    PriceResponse,
    LineItem,
    LineItemResponse,
    InsiderTrade,
    InsiderTradeResponse,
    CompanyFactsResponse,
)

# Global cache instance
_cache = get_cache()


def get_prices(ticker: str, start_date: str, end_date: str) -> List[Price]:
    """使用akshare获取A股价格数据"""
    # 创建缓存键
    cache_key = f"akshare_{ticker}_{start_date}_{end_date}"
    
    # 检查缓存
    if cached_data := _cache.get_prices(cache_key):
        return [Price(**price) for price in cached_data]

    try:
        # 将日期格式转换为akshare需要的格式 (YYYYMMDD)
        start_date_ak = datetime.datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y%m%d")
        end_date_ak = datetime.datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y%m%d")
        
        # 从akshare获取历史数据
        stock_data = ak.stock_zh_a_hist(
            symbol=ticker, 
            period="daily", 
            start_date=start_date_ak, 
            end_date=end_date_ak, 
            adjust=""  # 不复权
        )
        
        if stock_data is None or stock_data.empty:
            return []
        
        # 转换为Price对象
        prices = []
        for _, row in stock_data.iterrows():
            # 解析日期
            date_obj = pd.to_datetime(row['日期'])
            
            price = Price(
                time=date_obj.isoformat(),
                open=float(row['开盘']),
                high=float(row['最高']),
                low=float(row['最低']),
                close=float(row['收盘']),
                volume=int(row['成交量']),
                ticker=ticker
            )
            prices.append(price)
        
        # 按时间排序
        prices.sort(key=lambda x: x.time)
        
        # 缓存结果
        if prices:
            _cache.set_prices(cache_key, [p.model_dump() for p in prices])
        
        return prices
        
    except Exception as e:
        print(f"❌ 获取价格数据失败 {ticker}: {e}")
        return []


def get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> List[FinancialMetrics]:
    """使用akshare的新接口获取财务指标数据"""
    # 创建缓存键
    cache_key = f"akshare_financial_new_{ticker}_{period}_{end_date}_{limit}"
    
    # 检查缓存
    if cached_data := _cache.get_financial_metrics(cache_key):
        return [FinancialMetrics(**metric) for metric in cached_data]

    try:
        # 使用新的akshare接口获取更准确的财务数据
        print(f"🔍 使用新接口获取 {ticker} 的财务数据...")
        
        # 获取财务效益数据（利润表相关）
        benefit_data = ak.stock_financial_benefit_ths(symbol=ticker)
        
        # 获取财务负债数据（资产负债表相关）
        debt_data = ak.stock_financial_debt_ths(symbol=ticker)
        
        if benefit_data is None or benefit_data.empty:
            print(f"⚠️  未获取到 {ticker} 的财务效益数据")
            return []
            
        if debt_data is None or debt_data.empty:
            print(f"⚠️  未获取到 {ticker} 的财务负债数据")
            return []
        
        # 确保两个数据源有相同的报告期
        benefit_periods = set(benefit_data['报告期'].tolist())
        debt_periods = set(debt_data['报告期'].tolist())
        common_periods = benefit_periods.intersection(debt_periods)
        
        if not common_periods:
            print(f"⚠️  {ticker} 的利润表和资产负债表数据报告期不匹配")
            return []
        
        # 转换为FinancialMetrics对象
        financial_metrics = []
        
        # 取前limit个报告期
        sorted_periods = sorted(list(common_periods), reverse=True)[:limit]
        
        for report_period in sorted_periods:
            try:
                # 获取对应报告期的数据
                benefit_row = benefit_data[benefit_data['报告期'] == report_period].iloc[0]
                debt_row = debt_data[debt_data['报告期'] == report_period].iloc[0]
                
                # 安全提取数值的辅助函数
                def safe_extract_value(value, multiplier=1):
                    """安全提取数值，处理各种格式"""
                    if value in [None, 'False', False, '', 'nan']:
                        return None
                    try:
                        if isinstance(value, str):
                            # 处理中文单位
                            if '亿' in value:
                                return float(value.replace('亿', '')) * 100000000 * multiplier
                            elif '万' in value:
                                return float(value.replace('万', '')) * 10000 * multiplier
                            elif '%' in value:
                                return float(value.replace('%', ''))
                            else:
                                # 移除逗号等分隔符
                                clean_value = value.replace(',', '').replace(' ', '')
                                return float(clean_value) * multiplier
                        return float(value) * multiplier
                    except (ValueError, TypeError):
                        return None
                
                # 从利润表数据中提取关键指标
                revenue = safe_extract_value(benefit_row.get('*营业总收入'))
                net_income = safe_extract_value(benefit_row.get('*净利润'))
                gross_profit = safe_extract_value(benefit_row.get('毛利润'))  # 如果有的话
                operating_income = safe_extract_value(benefit_row.get('三、营业利润'))
                ebit = operating_income  # 营业利润近似EBIT
                
                # 从资产负债表数据中提取关键指标
                total_assets = safe_extract_value(debt_row.get('*资产合计'))
                total_debt = safe_extract_value(debt_row.get('*负债合计'))
                shareholders_equity = safe_extract_value(debt_row.get('*所有者权益（或股东权益）合计'))
                current_assets = safe_extract_value(debt_row.get('流动资产'))
                current_liabilities = safe_extract_value(debt_row.get('流动负债'))
                cash_and_cash_equivalents = safe_extract_value(debt_row.get('现金及存放中央银行款项'))
                
                # 计算派生指标
                def safe_ratio(numerator, denominator, percentage=True):
                    """安全计算比率"""
                    if numerator is None or denominator is None or denominator == 0:
                        return None
                    ratio = numerator / denominator
                    return ratio * 100 if percentage else ratio
                
                # 计算关键财务比率
                return_on_equity = safe_ratio(net_income, shareholders_equity)
                return_on_assets = safe_ratio(net_income, total_assets)
                operating_margin = safe_ratio(operating_income, revenue)
                net_margin = safe_ratio(net_income, revenue)
                gross_margin = safe_ratio(gross_profit, revenue) if gross_profit else None
                current_ratio = safe_ratio(current_assets, current_liabilities, False)
                debt_to_equity = safe_ratio(total_debt, shareholders_equity, False)
                
                # 创建FinancialMetrics对象
                financial_metric = FinancialMetrics(
                    report_period=str(report_period),
                    ticker=ticker,
                    period=period,
                    currency="CNY",  # A股数据，货币为人民币
                    
                    # 基础财务数据
                    revenue=revenue,
                    net_income=net_income,
                    gross_profit=gross_profit,
                    operating_income=operating_income,
                    ebit=ebit,
                    ebitda=None,  # 需要更详细的数据计算
                    
                    # 资产负债表项目
                    total_assets=total_assets,
                    current_assets=current_assets,
                    non_current_assets=safe_extract_value(total_assets) - safe_extract_value(current_assets) if total_assets and current_assets else None,
                    cash_and_cash_equivalents=cash_and_cash_equivalents,
                    total_debt=total_debt,
                    current_liabilities=current_liabilities,
                    non_current_liabilities=safe_extract_value(total_debt) - safe_extract_value(current_liabilities) if total_debt and current_liabilities else None,
                    shareholders_equity=shareholders_equity,
                    
                    # 财务比率
                    return_on_equity=return_on_equity,
                    return_on_assets=return_on_assets,
                    operating_margin=operating_margin,
                    net_margin=net_margin,
                    gross_margin=gross_margin,
                    current_ratio=current_ratio,
                    debt_to_equity=debt_to_equity,
                    
                    # 默认值的字段（这些需要额外数据计算或akshare不提供）
                    market_cap=None,
                    enterprise_value=None,
                    price_to_earnings_ratio=None,
                    price_to_book_ratio=None,
                    price_to_sales_ratio=None,
                    enterprise_value_to_ebitda_ratio=None,
                    enterprise_value_to_revenue_ratio=None,
                    free_cash_flow_yield=None,
                    peg_ratio=None,
                    return_on_invested_capital=None,
                    asset_turnover=None,
                    inventory_turnover=None,
                    receivables_turnover=None,
                    days_sales_outstanding=None,
                    operating_cycle=None,
                    working_capital_turnover=None,
                    cash_ratio=None,
                    operating_cash_flow_ratio=None,
                    debt_to_assets=safe_ratio(total_debt, total_assets, False),
                    interest_coverage=None,
                    revenue_growth=None,
                    earnings_growth=None,
                    book_value_growth=None,
                    earnings_per_share_growth=None,
                    free_cash_flow_growth=None,
                    operating_income_growth=None,
                    ebitda_growth=None,
                    payout_ratio=None,
                    earnings_per_share=safe_extract_value(benefit_row.get('（一）基本每股收益')),
                    book_value_per_share=safe_ratio(shareholders_equity, 19405918198, False) if shareholders_equity else None,  # 总股本
                    free_cash_flow_per_share=None,
                    quick_ratio=None,
                )
                
                financial_metrics.append(financial_metric)
                print(f"✅ 成功处理 {report_period} 的财务数据")
                
            except Exception as e:
                print(f"⚠️  处理报告期 {report_period} 的财务数据出错: {e}")
                continue
        
        # 缓存结果
        if financial_metrics:
            _cache.set_financial_metrics(cache_key, [m.model_dump() for m in financial_metrics])
            print(f"✅ 成功获取并缓存 {len(financial_metrics)} 条财务指标数据")
        
        return financial_metrics
        
    except Exception as e:
        print(f"❌ 获取财务指标失败 {ticker}: {e}")
        # 回退到原有方法
        print(f"🔄 尝试使用原有接口...")
        return get_financial_metrics_fallback(ticker, end_date, period, limit)


def get_financial_metrics_fallback(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> List[FinancialMetrics]:
    """回退方法：使用原有的akshare接口获取财务指标数据"""
    try:
        # 获取财务指标数据
        financial_data = ak.stock_financial_abstract_ths(symbol=ticker)
        
        if financial_data is None or financial_data.empty:
            return []
        
        # 转换为FinancialMetrics对象
        financial_metrics = []
        
        # 限制返回数量
        limited_data = financial_data.head(limit)
        
        for _, row in limited_data.iterrows():
            try:
                # 解析报告期
                report_date = str(row.get('报告期', ''))
                if report_date and report_date != 'False':
                    report_date_obj = pd.to_datetime(report_date)
                else:
                    # 如果没有报告期，使用end_date
                    report_date_obj = pd.to_datetime(end_date)
                
                # 提取财务指标，处理可能的None或'False'值
                def safe_float(value, default=None):
                    if value in [None, 'False', False, '']:
                        return default
                    try:
                        # 处理带单位的数字（如"1.13亿"）
                        if isinstance(value, str):
                            if '亿' in value:
                                return float(value.replace('亿', '')) * 100000000
                            elif '万' in value:
                                return float(value.replace('万', '')) * 10000
                            elif '%' in value:
                                return float(value.replace('%', ''))
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                financial_metric = FinancialMetrics(
                    report_period=report_date_obj.strftime("%Y-%m-%d"),
                    ticker=ticker,
                    # 必需字段，akshare没有提供的
                    period=period,  # 使用传入的period参数，默认是"ttm"
                    currency="CNY",  # A股数据，货币为人民币
                    # 基础财务数据
                    revenue=safe_float(row.get('营业总收入')),
                    net_income=safe_float(row.get('净利润')),
                    total_assets=safe_float(row.get('总资产')),
                    total_debt=safe_float(row.get('负债合计')),
                    shareholders_equity=safe_float(row.get('股东权益合计')),
                    # 比率指标
                    debt_to_equity=safe_float(row.get('产权比率')),
                    current_ratio=safe_float(row.get('流动比率')),
                    quick_ratio=safe_float(row.get('速动比率')),
                    # 其他可能的字段
                    gross_margin=safe_float(row.get('毛利率')),
                    operating_margin=safe_float(row.get('营业利润率')),
                    # 需要提供默认值的必需字段
                    market_cap=None,
                    enterprise_value=None,
                    price_to_earnings_ratio=None,
                    price_to_book_ratio=None,
                    price_to_sales_ratio=None,
                    enterprise_value_to_ebitda_ratio=None,
                    enterprise_value_to_revenue_ratio=None,
                    free_cash_flow_yield=None,
                    peg_ratio=None,
                    net_margin=None,
                    return_on_equity=safe_float(row.get('净资产收益率')),
                    return_on_assets=safe_float(row.get('总资产收益率')),
                    return_on_invested_capital=None,
                    asset_turnover=None,
                    inventory_turnover=None,
                    receivables_turnover=None,
                    days_sales_outstanding=None,
                    operating_cycle=None,
                    working_capital_turnover=None,
                    cash_ratio=None,
                    operating_cash_flow_ratio=None,
                    debt_to_assets=None,
                    interest_coverage=None,
                    revenue_growth=None,
                    earnings_growth=None,
                    book_value_growth=None,
                    earnings_per_share_growth=None,
                    free_cash_flow_growth=None,
                    operating_income_growth=None,
                    ebitda_growth=None,
                    payout_ratio=None,
                    earnings_per_share=None,
                    book_value_per_share=None,
                    free_cash_flow_per_share=None,
                )
                
                financial_metrics.append(financial_metric)
                
            except Exception as e:
                print(f"⚠️  处理财务指标数据出错: {e}")
                continue
        
        return financial_metrics
        
    except Exception as e:
        print(f"❌ 回退方法也失败 {ticker}: {e}")
        return []


def search_line_items(
    ticker: str,
    line_items: List[str],
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> List[LineItem]:
    """
    搜索财务报表条目 - 使用akshare的财务数据，支持动态字段
    """
    try:
        # 获取完整的财务数据
        financial_data = ak.stock_financial_abstract_ths(symbol=ticker)
        
        if financial_data is None or financial_data.empty:
            return []
        
        # 建立akshare字段名与标准字段名的映射
        field_mapping = {
            "net_income": "净利润",
            "revenue": "营业总收入",
            "total_assets": "总资产",
            "total_liabilities": "负债合计",
            "current_assets": "流动资产",
            "current_liabilities": "流动负债",
            "shareholders_equity": "股东权益合计",
            "earnings_per_share": "每股收益",
            "book_value_per_share": "每股净资产",
            "free_cash_flow": "经营现金流量净额",  # 近似值
            "depreciation": "折旧与摊销",
            "capex": "购建固定资产无形资产和其他长期资产支付的现金",
            "ebit": "营业利润",
            "ebitda": "息税折旧摊销前利润",
            "outstanding_shares": "总股本",
            "dividends_and_other_cash_distributions": "分派股利利润或偿付利息支付的现金",
            "operating_income": "营业利润",
            "gross_profit": "毛利润",
            "operating_expenses": "营业总成本",
            # 新增更多字段
            "cash_and_cash_equivalents": "货币资金",
            "inventory": "存货", 
            "accounts_receivable": "应收账款",
            "accounts_payable": "应付账款",
            "long_term_debt": "长期借款",
            "short_term_debt": "短期借款",
            "interest_expense": "利息费用",
            "income_tax_expense": "所得税费用",
            "research_and_development": "研发费用",
            "selling_general_administrative": "销售费用",
            "cost_of_revenue": "营业成本",
            "operating_cash_flow": "经营现金流量净额",
            "investing_cash_flow": "投资现金流量净额", 
            "financing_cash_flow": "筹资现金流量净额",
            "weighted_average_shares": "总股本",
            "diluted_weighted_average_shares": "总股本"
        }
        
        # 需要计算的字段
        calculated_fields = {
            "working_capital": ["流动资产", "流动负债"],  # 流动资产 - 流动负债
            "book_value": ["总资产", "负债合计"],  # 总资产 - 总负债
            "debt_to_equity": ["负债合计", "股东权益合计"],  # 负债/股东权益
            "total_debt": ["长期借款", "短期借款"],  # 长期借款 + 短期借款
            "net_debt": ["长期借款", "短期借款", "货币资金"],  # 总债务 - 现金
            "return_on_equity": ["净利润", "股东权益合计"],  # 净利润/股东权益
            "return_on_assets": ["净利润", "总资产"],  # 净利润/总资产
            "asset_turnover": ["营业总收入", "总资产"],  # 营业收入/总资产
            "current_ratio": ["流动资产", "流动负债"],  # 流动资产/流动负债
            "quick_ratio": ["流动资产", "存货", "流动负债"],  # (流动资产-存货)/流动负债
            "gross_margin": ["毛利润", "营业总收入"],  # 毛利润/营业收入
            "operating_margin": ["营业利润", "营业总收入"],  # 营业利润/营业收入
            "net_margin": ["净利润", "营业总收入"],  # 净利润/营业收入
        }
        
        def safe_float(value, default=0.0):
            """安全转换为浮点数"""
            if value in [None, 'False', False, '', 'nan']:
                return default
            try:
                # 处理带单位的数字（如"1.13亿"）
                if isinstance(value, str):
                    if '亿' in value:
                        return float(value.replace('亿', '')) * 100000000
                    elif '万' in value:
                        return float(value.replace('万', '')) * 10000
                    elif '%' in value:
                        return float(value.replace('%', ''))
                return float(value)
            except (ValueError, TypeError):
                return default
        
        def get_field_value(row, field_name):
            """获取字段值，支持直接映射和计算字段"""
            if field_name in field_mapping:
                # 直接映射字段
                ak_field = field_mapping[field_name]
                return safe_float(row.get(ak_field))
            elif field_name in calculated_fields:
                # 计算字段
                ak_fields = calculated_fields[field_name]
                if field_name == "working_capital":
                    current_assets = safe_float(row.get(ak_fields[0]))
                    current_liabilities = safe_float(row.get(ak_fields[1]))
                    return current_assets - current_liabilities
                elif field_name == "book_value":
                    total_assets = safe_float(row.get(ak_fields[0]))
                    total_liabilities = safe_float(row.get(ak_fields[1]))
                    return total_assets - total_liabilities
                elif field_name == "debt_to_equity":
                    total_debt = safe_float(row.get(ak_fields[0]))
                    equity = safe_float(row.get(ak_fields[1]))
                    return total_debt / equity if equity != 0 else 0.0
                elif field_name == "total_debt":
                    long_term_debt = safe_float(row.get(ak_fields[0]))
                    short_term_debt = safe_float(row.get(ak_fields[1]))
                    return long_term_debt + short_term_debt
                elif field_name == "net_debt":
                    long_term_debt = safe_float(row.get(ak_fields[0]))
                    short_term_debt = safe_float(row.get(ak_fields[1]))
                    cash = safe_float(row.get(ak_fields[2]))
                    return (long_term_debt + short_term_debt) - cash
                elif field_name == "return_on_equity":
                    net_income = safe_float(row.get(ak_fields[0]))
                    equity = safe_float(row.get(ak_fields[1]))
                    return (net_income / equity) * 100 if equity != 0 else 0.0
                elif field_name == "return_on_assets":
                    net_income = safe_float(row.get(ak_fields[0]))
                    assets = safe_float(row.get(ak_fields[1]))
                    return (net_income / assets) * 100 if assets != 0 else 0.0
                elif field_name == "asset_turnover":
                    revenue = safe_float(row.get(ak_fields[0]))
                    assets = safe_float(row.get(ak_fields[1]))
                    return revenue / assets if assets != 0 else 0.0
                elif field_name == "current_ratio":
                    current_assets = safe_float(row.get(ak_fields[0]))
                    current_liabilities = safe_float(row.get(ak_fields[1]))
                    return current_assets / current_liabilities if current_liabilities != 0 else 0.0
                elif field_name == "quick_ratio":
                    current_assets = safe_float(row.get(ak_fields[0]))
                    inventory = safe_float(row.get(ak_fields[1]))
                    current_liabilities = safe_float(row.get(ak_fields[2]))
                    return (current_assets - inventory) / current_liabilities if current_liabilities != 0 else 0.0
                elif field_name == "gross_margin":
                    gross_profit = safe_float(row.get(ak_fields[0]))
                    revenue = safe_float(row.get(ak_fields[1]))
                    return (gross_profit / revenue) * 100 if revenue != 0 else 0.0
                elif field_name == "operating_margin":
                    operating_income = safe_float(row.get(ak_fields[0]))
                    revenue = safe_float(row.get(ak_fields[1]))
                    return (operating_income / revenue) * 100 if revenue != 0 else 0.0
                elif field_name == "net_margin":
                    net_income = safe_float(row.get(ak_fields[0]))
                    revenue = safe_float(row.get(ak_fields[1]))
                    return (net_income / revenue) * 100 if revenue != 0 else 0.0
            
            # 如果找不到映射，尝试直接使用字段名
            return safe_float(row.get(field_name))
        
        # 构建LineItem结果
        line_items_result = []
        
        for _, row in financial_data.head(limit).iterrows():
            try:
                # 创建基础LineItem对象
                line_item_data = {
                    "ticker": ticker,
                    "report_period": str(row.get('报告期', end_date)),
                    "period": period,
                    "currency": "CNY",
                    "fiscal_year": str(row.get('报告期', end_date))[:4] if str(row.get('报告期', '')) != 'False' else end_date[:4],
                    "fiscal_period": "FY",
                    "line_item_name": line_items[0] if line_items else "净利润",
                    "line_item_value": str(get_field_value(row, line_items[0] if line_items else "net_income"))
                }
                
                # 为请求的每个line_item添加动态字段
                for field_name in line_items:
                    field_value = get_field_value(row, field_name)
                    line_item_data[field_name] = field_value
                
                # 创建LineItem对象（使用model_config = {"extra": "allow"}）
                line_item = LineItem(**line_item_data)
                line_items_result.append(line_item)
                
            except Exception as e:
                print(f"⚠️  处理LineItem数据出错: {e}")
                continue
        
        return line_items_result[:limit]
        
    except Exception as e:
        print(f"❌ 搜索财务条目失败 {ticker}: {e}")
        return []


def get_insider_trades(
    ticker: str,
    end_date: str,
    start_date: Optional[str] = None,
    limit: int = 1000,
) -> List[InsiderTrade]:
    """
    获取内部交易数据 - akshare暂不支持，返回空列表
    """
    print(f"⚠️  akshare暂不支持内部交易数据，ticker: {ticker}")
    return []


def get_company_news(
    ticker: str,
    end_date: str,
    start_date: Optional[str] = None,
    limit: int = 1000,
) -> List[CompanyNews]:
    """
    获取公司新闻数据 - 使用akshare的新闻接口
    """
    # 创建缓存键
    cache_key = f"akshare_news_{ticker}_{start_date or 'none'}_{end_date}_{limit}"
    
    # 检查缓存
    if cached_data := _cache.get_company_news(cache_key):
        return [CompanyNews(**news) for news in cached_data]

    try:
        # akshare的新闻接口可能需要不同的参数
        # 这里提供一个基础实现，实际使用时可能需要调整
        
        # 获取股票相关新闻（示例，具体接口需要根据akshare文档调整）
        try:
            # 尝试获取东方财富的个股新闻
            news_data = ak.stock_news_em(symbol=ticker)
            
            if news_data is None or news_data.empty:
                return []
            
            company_news = []
            for _, row in news_data.head(limit).iterrows():
                news = CompanyNews(
                    ticker=ticker,
                    date=str(row.get('发布时间', end_date)),
                    title=str(row.get('新闻标题', '')),
                    author=str(row.get('信息来源', 'akshare')),  # 使用信息来源作为作者
                    source=str(row.get('信息来源', 'akshare')),
                    url=str(row.get('新闻链接', '')),
                    content=str(row.get('新闻内容', ''))
                )
                company_news.append(news)
            
            # 缓存结果
            if company_news:
                _cache.set_company_news(cache_key, [news.model_dump() for news in company_news])
            
            return company_news
            
        except Exception:
            # 如果获取新闻失败，返回空列表
            return []
            
    except Exception as e:
        print(f"❌ 获取公司新闻失败 {ticker}: {e}")
        return []


def get_market_cap(ticker: str, end_date: str) -> Optional[float]:
    """
    获取市值数据 - 使用akshare的实时行情计算，添加容错处理
    """
    try:
        # 尝试多个备用接口
        retry_count = 3
        for attempt in range(retry_count):
            try:
                # 方法1: 获取实时行情数据
                real_time_data = ak.stock_zh_a_spot_em()
                
                if real_time_data is not None and not real_time_data.empty:
                    # 查找指定股票
                    stock_info = real_time_data[real_time_data['代码'] == ticker]
                    
                    if not stock_info.empty:
                        # 获取市值（如果有的话）
                        market_cap = stock_info.iloc[0].get('总市值', None)
                        
                        if market_cap is not None:
                            return float(market_cap)
                
                break  # 成功获取数据，退出重试循环
                
            except Exception as e:
                print(f"⚠️  获取市值重试 {attempt + 1}/{retry_count}: {e}")
                if attempt == retry_count - 1:
                    # 最后一次重试失败，尝试备用方法
                    try:
                        # 方法2: 尝试获取个股信息
                        stock_info = ak.stock_individual_info_em(symbol=ticker)
                        if stock_info is not None and not stock_info.empty:
                            # 从个股信息中获取市值
                            for _, row in stock_info.iterrows():
                                if row.get('item') == '总市值':
                                    market_cap_str = row.get('value', '')
                                    # 添加类型检查
                                    if isinstance(market_cap_str, (int, float)):
                                        return float(market_cap_str)
                                    elif isinstance(market_cap_str, str):
                                        if '亿' in market_cap_str:
                                            return float(market_cap_str.replace('亿', '')) * 100000000
                                        elif '万' in market_cap_str:
                                            return float(market_cap_str.replace('万', '')) * 10000
                                        else:
                                            # 尝试直接转换为数字
                                            try:
                                                return float(market_cap_str)
                                            except ValueError:
                                                continue
                        
                        print(f"ℹ️  使用备用方法获取市值也失败")
                        return None
                        
                    except Exception as backup_error:
                        print(f"ℹ️  备用方法获取市值失败: {backup_error}")
                        return None
        
        return None
        
    except Exception as e:
        print(f"ℹ️  获取市值完全失败 {ticker}: {e}")
        return None


def get_real_time_quotes(tickers: List[str]) -> List[dict]:
    """
    获取实时行情数据 - 添加容错处理和备用方案
    """
    try:
        retry_count = 3
        for attempt in range(retry_count):
            try:
                # 获取所有A股实时行情
                real_time_data = ak.stock_zh_a_spot_em()
                
                if real_time_data is not None and not real_time_data.empty:
                    # 筛选指定的股票
                    result = []
                    for ticker in tickers:
                        stock_info = real_time_data[real_time_data['代码'] == ticker]
                        
                        if not stock_info.empty:
                            row = stock_info.iloc[0]
                            result.append({
                                'ticker': ticker,
                                'name': str(row.get('名称', '')),
                                'price': float(row.get('最新价', 0)),
                                'open': float(row.get('今开', 0)),
                                'high': float(row.get('最高', 0)),
                                'low': float(row.get('最低', 0)),
                                'volume': int(row.get('成交量', 0)),
                                'amount': float(row.get('成交额', 0)),
                                'change_pct': float(row.get('涨跌幅', 0)),
                            })
                    
                    return result
                
                break  # 成功获取数据，退出重试循环
                
            except Exception as e:
                print(f"⚠️  获取实时行情重试 {attempt + 1}/{retry_count}: {e}")
                if attempt == retry_count - 1:
                    # 最后一次重试失败，尝试备用方法
                    try:
                        # 方法2: 逐个获取股票信息
                        result = []
                        for ticker in tickers:
                            try:
                                # 获取单个股票的实时价格
                                price_data = ak.stock_zh_a_hist(symbol=ticker, period="daily", adjust="")
                                if price_data is not None and not price_data.empty:
                                    latest = price_data.iloc[-1]
                                    result.append({
                                        'ticker': ticker,
                                        'name': f'股票{ticker}',
                                        'price': float(latest.get('收盘', 0)),
                                        'open': float(latest.get('开盘', 0)),
                                        'high': float(latest.get('最高', 0)),
                                        'low': float(latest.get('最低', 0)),
                                        'volume': int(latest.get('成交量', 0)),
                                        'amount': float(latest.get('成交额', 0)),
                                        'change_pct': 0.0,  # 无法计算涨跌幅
                                    })
                            except Exception:
                                continue
                        
                        return result
                        
                    except Exception as backup_error:
                        print(f"ℹ️  备用方法获取实时行情失败: {backup_error}")
                        return []
        
        return []
        
    except Exception as e:
        print(f"ℹ️  获取实时行情完全失败: {e}")
        return []


def prices_to_df(prices: List[Price]) -> pd.DataFrame:
    """将价格数据转换为DataFrame"""
    if not prices:
        return pd.DataFrame()
    
    df = pd.DataFrame([p.model_dump() for p in prices])
    df["Date"] = pd.to_datetime(df["time"])
    df.set_index("Date", inplace=True)
    numeric_cols = ["open", "close", "high", "low", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.sort_index(inplace=True)
    return df


def get_price_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取价格数据并转换为DataFrame"""
    prices = get_prices(ticker, start_date, end_date)
    return prices_to_df(prices)


# 测试函数
def test_akshare_api():
    """测试akshare API功能"""
    print("🚀 测试akshare API替换功能")
    
    # 测试获取价格数据
    try:
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        
        print(f"📅 测试日期范围: {start_date} 到 {end_date}")
        prices = get_prices("000001", start_date, end_date)
        print(f"✅ 获取到 {len(prices)} 条价格数据")
        
        if prices:
            print(f"最新价格: {prices[-1].close}")
            
        # 测试转换为DataFrame
        df = prices_to_df(prices)
        print(f"✅ DataFrame形状: {df.shape}")
        
    except Exception as e:
        print(f"❌ 价格数据测试失败: {e}")
    
    # 测试财务指标
    try:
        financial_metrics = get_financial_metrics("000001", end_date)
        print(f"✅ 获取到 {len(financial_metrics)} 条财务指标")
        
        if financial_metrics:
            print(f"第一条财务指标对象: {financial_metrics[0]}")
            print(f"第一条财务指标 - 报告期: {financial_metrics[0].report_period}")
            print(f"第一条财务指标 - 货币: {financial_metrics[0].currency}")
            print(f"第一条财务指标 - 期间: {financial_metrics[0].period}")
            
    except Exception as e:
        print(f"❌ 财务指标测试失败: {e}")
    
    # 测试实时行情
    try:
        quotes = get_real_time_quotes(["000001", "600036"])
        print(f"✅ 获取到 {len(quotes)} 条实时行情")
        for quote in quotes:
            print(f"  {quote['ticker']}: {quote['price']}")
    except Exception as e:
        print(f"❌ 实时行情测试失败: {e}")


def get_company_info(ticker: str) -> dict:
    """
    获取公司基本信息，包括行业、主营业务等Warren Buffett分析所需的信息
    """
    try:
        company_info = {
            'ticker': ticker,
            'basic_info': {},
            'business_info': {},
            'industry_info': {},
            'financial_summary': {}
        }
        
        # 获取个股基本信息
        try:
            individual_info = ak.stock_individual_info_em(symbol=ticker)
            if individual_info is not None and not individual_info.empty:
                for _, row in individual_info.iterrows():
                    item = str(row['item'])
                    value = str(row['value'])
                    
                    # 基本信息
                    if any(key in item for key in ['股票代码', '股票简称', '总股本', '流通股', '总市值', '流通市值', '上市时间']):
                        company_info['basic_info'][item] = value
                    
                    # 行业信息
                    elif '行业' in item:
                        company_info['industry_info'][item] = value
                    
                    # 主营业务相关
                    elif any(key in item for key in ['主营业务', '经营范围', '公司简介', '业务描述']):
                        company_info['business_info'][item] = value
                        
        except Exception as e:
            print(f"⚠️  获取个股基本信息失败: {e}")
        
        # 获取财务摘要信息用于Warren Buffett分析
        try:
            financial_data = ak.stock_financial_abstract_ths(symbol=ticker)
            if financial_data is not None and not financial_data.empty:
                latest = financial_data.iloc[0]
                
                # 提取Warren Buffett关注的关键指标
                key_metrics = {
                    'ROE': latest.get('净资产收益率'),
                    'ROA': latest.get('总资产收益率'), 
                    'debt_ratio': latest.get('产权比率'),
                    'current_ratio': latest.get('流动比率'),
                    'net_margin': latest.get('销售净利率'),
                    'gross_margin': latest.get('毛利率'),
                    'revenue': latest.get('营业总收入'),
                    'net_income': latest.get('净利润'),
                    'eps': latest.get('基本每股收益'),
                    'book_value_per_share': latest.get('每股净资产')
                }
                
                # 清理数据：移除None和'False'值
                company_info['financial_summary'] = {
                    k: v for k, v in key_metrics.items() 
                    if v not in [None, 'False', False, '']
                }
                
        except Exception as e:
            print(f"⚠️  获取财务摘要失败: {e}")
        
        # 添加Warren Buffett评估模板
        company_info['warren_buffett_analysis'] = {
            'moat_indicators': {
                'description': '护城河指标分析',
                'high_roe': company_info['financial_summary'].get('ROE', 'N/A'),
                'stable_margins': company_info['financial_summary'].get('net_margin', 'N/A'),
                'low_debt': company_info['financial_summary'].get('debt_ratio', 'N/A'),
                'strong_brand': '需要定性分析',  # 需要额外研究
                'market_position': '需要定性分析'  # 需要额外研究
            },
            'financial_strength': {
                'description': '财务实力评估',
                'profitability': {
                    'roe': company_info['financial_summary'].get('ROE', 'N/A'),
                    'roa': company_info['financial_summary'].get('ROA', 'N/A'),
                    'net_margin': company_info['financial_summary'].get('net_margin', 'N/A')
                },
                'debt_management': {
                    'debt_ratio': company_info['financial_summary'].get('debt_ratio', 'N/A'),
                    'current_ratio': company_info['financial_summary'].get('current_ratio', 'N/A')
                }
            },
            'business_quality': {
                'description': '业务质量评估',
                'industry': company_info['industry_info'].get('行业', '需要补充'),
                'business_model': '需要进一步研究',
                'competitive_advantage': '需要行业对比分析',
                'management_quality': '需要补充管理层信息'
            }
        }
        
        return company_info
        
    except Exception as e:
        print(f"❌ 获取公司信息失败 {ticker}: {e}")
        return {'ticker': ticker, 'error': str(e)}


def get_industry_analysis(ticker: str) -> dict:
    """
    获取行业分析数据，用于Warren Buffett的行业前景评估
    """
    try:
        # 首先获取股票的行业信息
        company_info = get_company_info(ticker)
        industry = company_info.get('industry_info', {}).get('行业', '')
        
        if not industry:
            return {'ticker': ticker, 'error': '无法确定行业分类'}
        
        industry_analysis = {
            'ticker': ticker,
            'industry': industry,
            'industry_overview': {},
            'peer_comparison': {},
            'industry_trends': {}
        }
        
        # 根据行业获取同行业股票进行对比
        try:
            if '银行' in industry:
                # 银行业分析
                bank_stocks = ['000001', '600036', '600000', '601166', '600015', '601328']
                industry_analysis['peer_stocks'] = bank_stocks
                industry_analysis['industry_characteristics'] = {
                    'capital_intensive': True,
                    'regulated': True,
                    'cyclical': True,
                    'moat_type': '监管护城河',
                    'key_metrics': ['ROE', 'NIM', 'NPL_ratio', 'capital_adequacy']
                }
                
            elif '酿酒' in industry:
                # 酿酒业分析
                alcohol_stocks = ['600519', '000858', '000596', '002304', '000799']
                industry_analysis['peer_stocks'] = alcohol_stocks
                industry_analysis['industry_characteristics'] = {
                    'capital_intensive': False,
                    'regulated': True,
                    'cyclical': False,
                    'moat_type': '品牌护城河',
                    'key_metrics': ['gross_margin', 'brand_premium', 'market_share']
                }
                
            else:
                industry_analysis['peer_stocks'] = []
                industry_analysis['industry_characteristics'] = {
                    'description': f'{industry}行业需要进一步分析'
                }
        
        except Exception as e:
            print(f"⚠️  行业对比分析失败: {e}")
        
        # 添加Warren Buffett行业评估框架
        industry_analysis['warren_buffett_industry_criteria'] = {
            'understandable_business': '需要定性评估',
            'long_term_prospects': '需要行业研究',
            'regulatory_environment': '需要政策分析',
            'competitive_dynamics': '需要竞争格局分析',
            'barriers_to_entry': '需要进入壁垒分析',
            'pricing_power': '需要定价能力分析'
        }
        
        return industry_analysis
        
    except Exception as e:
        print(f"❌ 行业分析失败 {ticker}: {e}")
        return {'ticker': ticker, 'error': str(e)}


def get_warren_buffett_analysis(ticker: str) -> dict:
    """
    进行Warren Buffett式的综合投资分析
    整合公司信息、财务指标、行业分析等
    """
    try:
        print(f"🔍 开始Warren Buffett式分析: {ticker}")
        
        analysis = {
            'ticker': ticker,
            'analysis_date': datetime.datetime.now().strftime("%Y-%m-%d"),
            'company_info': {},
            'industry_analysis': {},
            'financial_metrics': [],
            'warren_buffett_score': {},
            'investment_thesis': {},
            'risks_and_concerns': {},
            'final_assessment': {}
        }
        
        # 1. 获取公司基本信息
        analysis['company_info'] = get_company_info(ticker)
        
        # 2. 获取行业分析
        analysis['industry_analysis'] = get_industry_analysis(ticker)
        
        # 3. 获取最新财务指标
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        financial_metrics = get_financial_metrics(ticker, end_date, limit=5)
        analysis['financial_metrics'] = [m.model_dump() for m in financial_metrics]
        
        # 4. Warren Buffett评分系统
        score_components = {
            'business_understandability': 0,  # 0-20分
            'competitive_advantage': 0,       # 0-25分  
            'financial_strength': 0,         # 0-25分
            'management_quality': 0,         # 0-15分
            'valuation_attractiveness': 0    # 0-15分
        }
        
        # 财务实力评分（基于可获得的数据）
        if financial_metrics and len(financial_metrics) > 0:
            latest_metrics = financial_metrics[0]
            
            # ROE评分
            if latest_metrics.return_on_equity:
                if latest_metrics.return_on_equity > 15:
                    score_components['financial_strength'] += 10
                elif latest_metrics.return_on_equity > 10:
                    score_components['financial_strength'] += 7
                elif latest_metrics.return_on_equity > 5:
                    score_components['financial_strength'] += 4
            
            # 债务水平评分
            if latest_metrics.debt_to_equity:
                if latest_metrics.debt_to_equity < 0.3:
                    score_components['financial_strength'] += 8
                elif latest_metrics.debt_to_equity < 0.6:
                    score_components['financial_strength'] += 5
                elif latest_metrics.debt_to_equity < 1.0:
                    score_components['financial_strength'] += 2
            
            # 盈利能力评分
            if latest_metrics.net_margin:
                if latest_metrics.net_margin > 20:
                    score_components['financial_strength'] += 7
                elif latest_metrics.net_margin > 10:
                    score_components['financial_strength'] += 4
                elif latest_metrics.net_margin > 5:
                    score_components['financial_strength'] += 2
        
        # 行业评分（基于行业特征）
        industry = analysis['industry_analysis'].get('industry', '')
        if '银行' in industry:
            score_components['business_understandability'] = 15  # 银行业务相对简单
            score_components['competitive_advantage'] = 12      # 有监管护城河但竞争激烈
        elif '酿酒' in industry:
            score_components['business_understandability'] = 18  # 酿酒业务简单易懂
            score_components['competitive_advantage'] = 20      # 品牌护城河强
        
        # 计算总分
        total_score = sum(score_components.values())
        analysis['warren_buffett_score'] = {
            'components': score_components,
            'total_score': total_score,
            'max_score': 100,
            'grade': 'A' if total_score >= 80 else 'B' if total_score >= 60 else 'C' if total_score >= 40 else 'D',
            'interpretation': {
                'A (80-100)': '优秀投资标的',
                'B (60-79)': '良好投资标的', 
                'C (40-59)': '一般投资标的',
                'D (0-39)': '需要谨慎考虑'
            }
        }
        
        # 5. 投资论点
        analysis['investment_thesis'] = {
            'strengths': [],
            'opportunities': [],
            'competitive_moat': '需要进一步研究',
            'growth_prospects': '需要行业和公司前景分析'
        }
        
        # 6. 风险和关注点
        analysis['risks_and_concerns'] = {
            'business_risks': '需要行业分析',
            'financial_risks': '需要深入财务分析', 
            'regulatory_risks': '需要政策环境分析',
            'competitive_risks': '需要竞争格局分析'
        }
        
        # 7. 最终评估
        analysis['final_assessment'] = {
            'recommendation': '需要更多定性分析',
            'target_price': '需要估值模型',
            'time_horizon': '长期投资（3-5年以上）',
            'confidence_level': '中等（数据有限）',
            'next_steps': [
                '深入研究商业模式和竞争优势',
                '分析管理层质量和公司治理',
                '评估行业长期前景',
                '建立估值模型',
                '监控关键财务指标变化'
            ]
        }
        
        return analysis
        
    except Exception as e:
        print(f"❌ Warren Buffett分析失败 {ticker}: {e}")
        return {'ticker': ticker, 'error': str(e)}


def get_industry_peers(ticker: str) -> dict:
    """
    获取同行业股票列表，用于对比分析
    """
    try:
        # 首先获取股票的行业信息
        company_info = get_company_info(ticker)
        industry = company_info.get('industry_info', {}).get('行业', '')
        
        result = {
            'ticker': ticker,
            'industry': industry,
            'peer_stocks': [],
            'industry_summary': {}
        }
        
        if not industry:
            return result
        
        # 根据行业获取同行股票
        try:
            # 尝试不同的行业名称匹配
            industry_keywords = [industry]
            if '银行' in industry:
                industry_keywords.append('银行')
            elif '汽车' in industry:
                industry_keywords.extend(['汽车', '汽车整车'])
            elif '酿酒' in industry or '白酒' in industry:
                industry_keywords.extend(['酿酒', '白酒'])
            elif '医药' in industry:
                industry_keywords.extend(['医药', '医疗'])
            elif '房地产' in industry:
                industry_keywords.extend(['房地产', '地产'])
            
            # 尝试获取行业成分股
            for keyword in industry_keywords:
                try:
                    industry_stocks = ak.stock_board_industry_cons_em(symbol=keyword)
                    if industry_stocks is not None and not industry_stocks.empty:
                        # 获取同行股票信息
                        peers = []
                        for _, row in industry_stocks.head(20).iterrows():  # 限制20只股票
                            peer_info = {
                                'ticker': str(row.get('代码', '')),
                                'name': str(row.get('名称', '')),
                                'price': float(row.get('最新价', 0)) if row.get('最新价') != '-' else 0,
                                'change_pct': float(row.get('涨跌幅', 0)) if row.get('涨跌幅') != '-' else 0,
                                'pe_ratio': str(row.get('市盈率-动态', 'N/A')),
                                'pb_ratio': str(row.get('市净率', 'N/A')),
                                'market_cap': str(row.get('总市值', 'N/A'))
                            }
                            peers.append(peer_info)
                        
                        result['peer_stocks'] = peers
                        result['industry_summary'] = {
                            'total_stocks': len(peers),
                            'avg_change_pct': sum(p['change_pct'] for p in peers if p['change_pct'] != 0) / max(1, sum(1 for p in peers if p['change_pct'] != 0)),
                            'industry_keyword': keyword
                        }
                        break
                        
                except Exception as e:
                    print(f"⚠️  尝试行业关键词 '{keyword}' 失败: {e}")
                    continue
        
        except Exception as e:
            print(f"⚠️  获取同行业股票失败: {e}")
        
        return result
        
    except Exception as e:
        print(f"❌ 获取行业同行失败 {ticker}: {e}")
        return {'ticker': ticker, 'error': str(e)}


def get_all_industries() -> List[dict]:
    """
    获取所有行业分类信息
    """
    try:
        industries = []
        
        # 获取申万行业分类
        industry_data = ak.stock_board_industry_name_em()
        if industry_data is not None and not industry_data.empty:
            for _, row in industry_data.iterrows():
                industry_info = {
                    'name': str(row.get('板块名称', '')),
                    'code': str(row.get('板块代码', '')),
                    'stock_count': int(row.get('公司家数', 0)) if row.get('公司家数') != '-' else 0,
                    'avg_price': float(row.get('平均价格', 0)) if row.get('平均价格') != '-' else 0,
                    'change_pct': float(row.get('涨跌幅', 0)) if row.get('涨跌幅') != '-' else 0,
                    'turnover_rate': float(row.get('换手率', 0)) if row.get('换手率') != '-' else 0,
                    'pe_ratio': str(row.get('市盈率', 'N/A')),
                    'market_cap': str(row.get('总市值', 'N/A'))
                }
                industries.append(industry_info)
        
        return industries
        
    except Exception as e:
        print(f"❌ 获取行业分类失败: {e}")
        return []


def get_concept_info(ticker: str) -> dict:
    """
    获取股票概念板块信息
    """
    try:
        result = {
            'ticker': ticker,
            'concepts': [],
            'hot_concepts': []
        }
        
        # 获取概念板块信息
        try:
            concept_data = ak.stock_board_concept_name_em()
            if concept_data is not None and not concept_data.empty:
                # 获取热门概念（按涨跌幅排序）
                hot_concepts = concept_data.head(20)
                for _, row in hot_concepts.iterrows():
                    concept_info = {
                        'name': str(row.get('板块名称', '')),
                        'code': str(row.get('板块代码', '')),
                        'stock_count': int(row.get('公司家数', 0)) if row.get('公司家数') != '-' else 0,
                        'change_pct': float(row.get('涨跌幅', 0)) if row.get('涨跌幅') != '-' else 0,
                        'turnover_rate': float(row.get('换手率', 0)) if row.get('换手率') != '-' else 0,
                        'pe_ratio': str(row.get('市盈率', 'N/A')),
                        'market_cap': str(row.get('总市值', 'N/A'))
                    }
                    result['hot_concepts'].append(concept_info)
        
        except Exception as e:
            print(f"⚠️  获取概念信息失败: {e}")
        
        return result
        
    except Exception as e:
        print(f"❌ 获取概念信息失败 {ticker}: {e}")
        return {'ticker': ticker, 'error': str(e)}


def get_enhanced_warren_buffett_analysis(ticker: str) -> dict:
    """
    增强版Warren Buffett分析，整合行业对比和概念分析
    """
    try:
        print(f"🔍 开始增强版Warren Buffett式分析: {ticker}")
        
        # 获取基础分析
        base_analysis = get_warren_buffett_analysis(ticker)
        
        # 添加行业对比分析
        print("🏭 获取行业同行对比数据...")
        peer_analysis = get_industry_peers(ticker)
        base_analysis['peer_analysis'] = peer_analysis
        
        # 添加概念板块分析
        print("💡 获取概念板块信息...")
        concept_analysis = get_concept_info(ticker)
        base_analysis['concept_analysis'] = concept_analysis
        
        # 增强评分系统 - 加入同行对比
        if 'warren_buffett_score' in base_analysis and peer_analysis.get('peer_stocks'):
            score_components = base_analysis['warren_buffett_score']['components']
            
            # 同行对比评分（基于相对表现）
            peers = peer_analysis['peer_stocks']
            target_ticker_data = None
            
            # 找到目标股票在同行中的数据
            for peer in peers:
                if peer['ticker'] == ticker:
                    target_ticker_data = peer
                    break
            
            if target_ticker_data:
                # 涨跌幅排名评分
                change_pcts = [p['change_pct'] for p in peers if p['change_pct'] != 0]
                if change_pcts:
                    target_change = target_ticker_data['change_pct']
                    better_count = sum(1 for pct in change_pcts if pct < target_change)
                    relative_performance = better_count / len(change_pcts)
                    
                    # 相对表现好的股票获得额外分数
                    if relative_performance > 0.8:
                        score_components['competitive_advantage'] += 5
                    elif relative_performance > 0.6:
                        score_components['competitive_advantage'] += 3
                    elif relative_performance > 0.4:
                        score_components['competitive_advantage'] += 1
            
            # 重新计算总分
            total_score = sum(score_components.values())
            base_analysis['warren_buffett_score']['total_score'] = total_score
            base_analysis['warren_buffett_score']['grade'] = (
                'A' if total_score >= 80 else 
                'B' if total_score >= 60 else 
                'C' if total_score >= 40 else 
                'D'
            )
        
        # 增强投资建议
        peer_count = len(peer_analysis.get('peer_stocks', []))
        if peer_count > 0:
            base_analysis['enhanced_insights'] = {
                'peer_comparison': {
                    'total_peers': peer_count,
                    'industry': peer_analysis.get('industry', 'N/A'),
                    'relative_analysis': '基于同行对比的相对评估'
                },
                'market_context': {
                    'hot_concepts_count': len(concept_analysis.get('hot_concepts', [])),
                    'concept_exposure': '概念板块曝光度分析'
                },
                'enhanced_recommendation': {
                    'context': '结合行业对比和概念分析的综合建议',
                    'peer_strength': '同行业相对地位评估',
                    'market_timing': '基于概念热度的时机分析'
                }
            }
        
        return base_analysis
        
    except Exception as e:
        print(f"❌ 增强版Warren Buffett分析失败 {ticker}: {e}")
        return {'ticker': ticker, 'error': str(e)}


def get_valuation_metrics(ticker: str) -> dict:
    """
    获取完整的估值指标，包括市盈率、市净率、股价等Warren Buffett分析所需的关键数据
    """
    try:
        valuation_data = {
            'ticker': ticker,
            'current_price': None,
            'pe_ratio': None,
            'pb_ratio': None,
            'ps_ratio': None,
            'market_cap': None,
            'price_data': {},
            'valuation_ratios': {},
            'per_share_metrics': {}
        }
        
        # 1. 获取当前股价
        try:
            real_time_quotes = get_real_time_quotes([ticker])
            if real_time_quotes:
                current_quote = real_time_quotes[0]
                valuation_data['current_price'] = current_quote.get('price', 0)
                valuation_data['price_data'] = {
                    'current_price': current_quote.get('price', 0),
                    'open': current_quote.get('open', 0),
                    'high': current_quote.get('high', 0),
                    'low': current_quote.get('low', 0),
                    'change_pct': current_quote.get('change_pct', 0),
                    'volume': current_quote.get('volume', 0),
                    'amount': current_quote.get('amount', 0)
                }
        except Exception as e:
            print(f"⚠️  获取实时股价失败: {e}")
        
        # 2. 获取市值
        try:
            market_cap = get_market_cap(ticker, datetime.datetime.now().strftime("%Y-%m-%d"))
            valuation_data['market_cap'] = market_cap
        except Exception as e:
            print(f"⚠️  获取市值失败: {e}")
        
        # 3. 从个股信息中获取估值比率
        try:
            individual_info = ak.stock_individual_info_em(symbol=ticker)
            if individual_info is not None and not individual_info.empty:
                for _, row in individual_info.iterrows():
                    item = str(row['item'])
                    value = str(row['value'])
                    
                    # 估值比率
                    if '市盈率' in item:
                        try:
                            pe_value = float(value) if value not in ['False', '', '-'] else None
                            valuation_data['pe_ratio'] = pe_value
                            valuation_data['valuation_ratios']['pe_ratio'] = pe_value
                        except ValueError:
                            pass
                    elif '市净率' in item:
                        try:
                            pb_value = float(value) if value not in ['False', '', '-'] else None
                            valuation_data['pb_ratio'] = pb_value
                            valuation_data['valuation_ratios']['pb_ratio'] = pb_value
                        except ValueError:
                            pass
                    elif '市销率' in item:
                        try:
                            ps_value = float(value) if value not in ['False', '', '-'] else None
                            valuation_data['ps_ratio'] = ps_value
                            valuation_data['valuation_ratios']['ps_ratio'] = ps_value
                        except ValueError:
                            pass
                    
                    # 每股指标
                    elif '每股收益' in item:
                        try:
                            eps_value = float(value) if value not in ['False', '', '-'] else None
                            valuation_data['per_share_metrics']['eps'] = eps_value
                        except ValueError:
                            pass
                    elif '每股净资产' in item:
                        try:
                            bvps_value = float(value) if value not in ['False', '', '-'] else None
                            valuation_data['per_share_metrics']['book_value_per_share'] = bvps_value
                        except ValueError:
                            pass
                    elif '每股营业收入' in item:
                        try:
                            sps_value = float(value) if value not in ['False', '', '-'] else None
                            valuation_data['per_share_metrics']['sales_per_share'] = sps_value
                        except ValueError:
                            pass
                    
        except Exception as e:
            print(f"⚠️  从个股信息获取估值数据失败: {e}")
        
        # 4. 尝试从行情数据中获取更多估值指标
        try:
            spot_data = ak.stock_zh_a_spot_em()
            if spot_data is not None and not spot_data.empty:
                stock_row = spot_data[spot_data['代码'] == ticker]
                if not stock_row.empty:
                    row = stock_row.iloc[0]
                    
                    # 更新价格数据
                    if not valuation_data['current_price']:
                        valuation_data['current_price'] = float(row.get('最新价', 0))
                    
                    # 估值比率
                    if not valuation_data['pe_ratio']:
                        pe_val = row.get('市盈率-动态', None)
                        if pe_val is not None and pe_val != '-':
                            try:
                                valuation_data['pe_ratio'] = float(pe_val)
                                valuation_data['valuation_ratios']['pe_ratio'] = float(pe_val)
                            except ValueError:
                                pass
                    
                    if not valuation_data['pb_ratio']:
                        pb_val = row.get('市净率', None)
                        if pb_val is not None and pb_val != '-':
                            try:
                                valuation_data['pb_ratio'] = float(pb_val)
                                valuation_data['valuation_ratios']['pb_ratio'] = float(pb_val)
                            except ValueError:
                                pass
                    
                    # 市值
                    if not valuation_data['market_cap']:
                        mc_val = row.get('总市值', None)
                        if mc_val is not None and mc_val != '-':
                            try:
                                valuation_data['market_cap'] = float(mc_val)
                            except ValueError:
                                pass
        
        except Exception as e:
            print(f"⚠️  从行情数据获取估值指标失败: {e}")
        
        # 5. 计算派生指标
        try:
            if all([valuation_data['current_price'], valuation_data['per_share_metrics'].get('eps')]):
                current_price = valuation_data['current_price']
                eps = valuation_data['per_share_metrics']['eps']
                if eps > 0:
                    calculated_pe = current_price / eps
                    if not valuation_data['pe_ratio']:
                        valuation_data['pe_ratio'] = calculated_pe
                        valuation_data['valuation_ratios']['pe_ratio_calculated'] = calculated_pe
            
            if all([valuation_data['current_price'], valuation_data['per_share_metrics'].get('book_value_per_share')]):
                current_price = valuation_data['current_price']
                bvps = valuation_data['per_share_metrics']['book_value_per_share']
                if bvps > 0:
                    calculated_pb = current_price / bvps
                    if not valuation_data['pb_ratio']:
                        valuation_data['pb_ratio'] = calculated_pb
                        valuation_data['valuation_ratios']['pb_ratio_calculated'] = calculated_pb
            
            if all([valuation_data['current_price'], valuation_data['per_share_metrics'].get('sales_per_share')]):
                current_price = valuation_data['current_price']
                sps = valuation_data['per_share_metrics']['sales_per_share']
                if sps > 0:
                    calculated_ps = current_price / sps
                    if not valuation_data['ps_ratio']:
                        valuation_data['ps_ratio'] = calculated_ps
                        valuation_data['valuation_ratios']['ps_ratio_calculated'] = calculated_ps
                        
        except Exception as e:
            print(f"⚠️  计算派生估值指标失败: {e}")
        
        # 6. 添加Warren Buffett式估值评估
        valuation_data['warren_buffett_valuation'] = {
            'current_price': valuation_data['current_price'],
            'pe_assessment': analyze_pe_ratio(valuation_data['pe_ratio']),
            'pb_assessment': analyze_pb_ratio(valuation_data['pb_ratio']),
            'overall_valuation': 'undetermined'
        }
        
        # 综合估值评估
        if valuation_data['pe_ratio'] and valuation_data['pb_ratio']:
            pe_score = get_valuation_score(valuation_data['pe_ratio'], 'pe')
            pb_score = get_valuation_score(valuation_data['pb_ratio'], 'pb')
            avg_score = (pe_score + pb_score) / 2
            
            if avg_score >= 80:
                valuation_data['warren_buffett_valuation']['overall_valuation'] = 'attractive'
            elif avg_score >= 60:
                valuation_data['warren_buffett_valuation']['overall_valuation'] = 'fair'
            elif avg_score >= 40:
                valuation_data['warren_buffett_valuation']['overall_valuation'] = 'expensive'
            else:
                valuation_data['warren_buffett_valuation']['overall_valuation'] = 'overvalued'
        
        return valuation_data
        
    except Exception as e:
        print(f"❌ 获取估值指标失败 {ticker}: {e}")
        return {'ticker': ticker, 'error': str(e)}


def analyze_pe_ratio(pe_ratio: float) -> dict:
    """分析市盈率的Warren Buffett式评估"""
    if pe_ratio is None:
        return {'assessment': 'unknown', 'reason': '市盈率数据不可用'}
    
    if pe_ratio <= 0:
        return {'assessment': 'negative_earnings', 'reason': '公司当前亏损'}
    elif pe_ratio < 10:
        return {'assessment': 'very_attractive', 'reason': '市盈率极低，非常有吸引力'}
    elif pe_ratio < 15:
        return {'assessment': 'attractive', 'reason': '市盈率较低，有吸引力'}
    elif pe_ratio < 20:
        return {'assessment': 'fair', 'reason': '市盈率合理'}
    elif pe_ratio < 30:
        return {'assessment': 'expensive', 'reason': '市盈率偏高'}
    else:
        return {'assessment': 'very_expensive', 'reason': '市盈率过高，风险较大'}


def analyze_pb_ratio(pb_ratio: float) -> dict:
    """分析市净率的Warren Buffett式评估"""
    if pb_ratio is None:
        return {'assessment': 'unknown', 'reason': '市净率数据不可用'}
    
    if pb_ratio <= 0:
        return {'assessment': 'negative_book_value', 'reason': '公司净资产为负'}
    elif pb_ratio < 1:
        return {'assessment': 'very_attractive', 'reason': '低于净资产价值，极具吸引力'}
    elif pb_ratio < 1.5:
        return {'assessment': 'attractive', 'reason': '市净率较低，有投资价值'}
    elif pb_ratio < 2.5:
        return {'assessment': 'fair', 'reason': '市净率合理'}
    elif pb_ratio < 4:
        return {'assessment': 'expensive', 'reason': '市净率偏高'}
    else:
        return {'assessment': 'very_expensive', 'reason': '市净率过高，估值过高'}


def get_valuation_score(ratio: float, ratio_type: str) -> int:
    """获取估值指标的评分（0-100分）"""
    if ratio is None:
        return 50  # 中性分数
    
    if ratio_type == 'pe':
        if ratio <= 0:
            return 0  # 亏损
        elif ratio < 10:
            return 95
        elif ratio < 15:
            return 85
        elif ratio < 20:
            return 70
        elif ratio < 30:
            return 40
        else:
            return 10
    
    elif ratio_type == 'pb':
        if ratio <= 0:
            return 0  # 负净资产
        elif ratio < 1:
            return 95
        elif ratio < 1.5:
            return 85
        elif ratio < 2.5:
            return 70
        elif ratio < 4:
            return 40
        else:
            return 10
    
    return 50  # 默认中性分数


if __name__ == "__main__":
    test_akshare_api() 