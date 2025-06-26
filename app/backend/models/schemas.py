from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from src.llm.models import ModelProvider


class AgentModelConfig(BaseModel):
    agent_id: str
    model_name: Optional[str] = None
    model_provider: Optional[ModelProvider] = None


class HedgeFundResponse(BaseModel):
    decisions: dict
    analyst_signals: dict


class ErrorResponse(BaseModel):
    message: str
    error: str | None = None


class HedgeFundRequest(BaseModel):
    tickers: List[str]
    selected_agents: List[str]
    agent_models: Optional[List[AgentModelConfig]] = None
    end_date: Optional[str] = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    start_date: Optional[str] = None
    model_name: str = "gpt-4o"
    model_provider: ModelProvider = ModelProvider.OPENAI
    initial_cash: float = 100000.0
    margin_requirement: float = 0.0

    def get_start_date(self) -> str:
        """Calculate start date if not provided"""
        if self.start_date:
            return self.start_date
        return (datetime.strptime(self.end_date, "%Y-%m-%d") - timedelta(days=90)).strftime("%Y-%m-%d")

    def get_agent_model_config(self, agent_id: str) -> tuple[str, ModelProvider]:
        """Get model configuration for a specific agent"""
        if self.agent_models:
            for config in self.agent_models:
                if config.agent_id == agent_id:
                    return (
                        config.model_name or self.model_name,
                        config.model_provider or self.model_provider
                    )
        # Fallback to global model settings
        return self.model_name, self.model_provider


# Flow-related schemas
class FlowCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    viewport: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    is_template: bool = False
    tags: Optional[List[str]] = None


class FlowUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    viewport: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    is_template: Optional[bool] = None
    tags: Optional[List[str]] = None


class FlowResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    viewport: Optional[Dict[str, Any]]
    data: Optional[Dict[str, Any]]
    is_template: bool
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class FlowSummaryResponse(BaseModel):
    """Lightweight flow response without nodes/edges for listing"""
    id: int
    name: str
    description: Optional[str]
    is_template: bool
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Stock-related schemas
class StockInfoResponse(BaseModel):
    """股票基本信息响应"""
    ticker: str
    name: str
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    description: Optional[str] = None


class StockPriceResponse(BaseModel):
    """股票价格响应"""
    ticker: str
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class StockFinancialMetricsResponse(BaseModel):
    """股票财务指标响应"""
    ticker: str
    report_period: str
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    total_assets: Optional[float] = None
    total_debt: Optional[float] = None
    shareholders_equity: Optional[float] = None
    return_on_equity: Optional[float] = None
    return_on_assets: Optional[float] = None
    debt_to_equity: Optional[float] = None


class StockSearchRequest(BaseModel):
    """股票搜索请求"""
    keyword: str = Field(..., min_length=1, max_length=100)
    limit: int = Field(default=10, ge=1, le=50)


class StockPriceRequest(BaseModel):
    """股票价格查询请求"""
    ticker: str = Field(..., min_length=1, max_length=20)
    start_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    end_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')


class StockAnalysisResponse(BaseModel):
    """股票分析响应"""
    ticker: str
    analysis_type: str
    score: Optional[int] = None
    recommendation: Optional[str] = None
    key_metrics: Optional[Dict[str, Any]] = None
    analysis_details: Optional[Dict[str, Any]] = None


class IndustryAnalysisResponse(BaseModel):
    """行业分析响应"""
    industry_name: str
    total_companies: int
    average_pe: Optional[float] = None
    average_pb: Optional[float] = None
    top_companies: List[Dict[str, Any]] = []
    industry_trends: Optional[Dict[str, Any]] = None


class StockNewsResponse(BaseModel):
    """股票新闻响应"""
    ticker: str
    title: str
    content: Optional[str] = None
    publish_time: str
    source: Optional[str] = None
    url: Optional[str] = None


class LimitUpStockResponse(BaseModel):
    """涨停股池响应"""
    序号: int
    代码: str
    名称: str
    涨跌幅: float
    最新价: float
    成交额: int
    流通市值: float
    总市值: float
    换手率: float
    封板资金: int
    首次封板时间: Optional[str] = None
    最后封板时间: Optional[str] = None
    炸板次数: int
    涨停统计: Optional[str] = None
    连板数: int
    所属行业: Optional[str] = None


class LimitUpPoolRequest(BaseModel):
    """涨停股池查询请求"""
    date: str = Field(..., pattern=r'^\d{8}$', description="查询日期，格式: YYYYMMDD")


class StrongStockResponse(BaseModel):
    """强势股池响应"""
    序号: int
    代码: str
    名称: str
    涨跌幅: float
    最新价: float
    涨停价: float
    成交额: int
    流通市值: float
    总市值: float
    换手率: float
    涨速: float
    是否新高: Optional[str] = None
    量比: float
    涨停统计: Optional[str] = None
    入选理由: Optional[str] = None
    所属行业: Optional[str] = None


class StrongPoolRequest(BaseModel):
    """强势股池查询请求"""
    date: str = Field(..., pattern=r'^\d{8}$', description="查询日期，格式: YYYYMMDD")


class SubNewStockResponse(BaseModel):
    """次新股池响应"""
    序号: int
    代码: str
    名称: str
    涨跌幅: float
    最新价: float
    涨停价: float
    成交额: int
    流通市值: float
    总市值: float
    转手率: float
    开板几日: int
    开板日期: int
    上市日期: int
    是否新高: int
    涨停统计: Optional[str] = None
    所属行业: Optional[str] = None


class SubNewPoolRequest(BaseModel):
    """次新股池查询请求"""
    date: str = Field(..., pattern=r'^\d{8}$', description="查询日期，格式: YYYYMMDD")


class ExplodeBoardStockResponse(BaseModel):
    """炸板股池响应"""
    序号: int
    代码: str
    名称: str
    涨跌幅: float
    最新价: float
    涨停价: float
    成交额: int
    流通市值: float
    总市值: float
    换手率: float
    涨速: int
    首次封板时间: Optional[str] = None
    炸板次数: int
    涨停统计: int
    振幅: Optional[str] = None
    所属行业: Optional[str] = None


class ExplodeBoardPoolRequest(BaseModel):
    """炸板股池查询请求"""
    date: str = Field(..., pattern=r'^\d{8}$', description="查询日期，格式: YYYYMMDD")


class FallLimitStockResponse(BaseModel):
    """跌停股池响应"""
    序号: int
    代码: str
    名称: str
    涨跌幅: float
    最新价: float
    成交额: int
    流通市值: float
    总市值: float
    动态市盈率: float
    换手率: float
    封单资金: int
    最后封板时间: Optional[str] = None
    板上成交额: int
    连续跌停: int
    开板次数: int
    所属行业: Optional[str] = None


class FallLimitPoolRequest(BaseModel):
    """跌停股池查询请求"""
    date: str = Field(..., pattern=r'^\d{8}$', description="查询日期，格式: YYYYMMDD")
