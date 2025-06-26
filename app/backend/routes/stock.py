from fastapi import APIRouter, HTTPException
from typing import List

from app.backend.models.schemas import (
    ErrorResponse,
    LimitUpStockResponse,
    LimitUpPoolRequest,
    StrongStockResponse,
    StrongPoolRequest,
    SubNewStockResponse,
    SubNewPoolRequest,
    ExplodeBoardStockResponse,
    ExplodeBoardPoolRequest,
    FallLimitStockResponse,
    FallLimitPoolRequest
)
from app.backend.services.stock_service import stock_service

router = APIRouter(prefix="/stock", tags=["stock"])


@router.get(
    "/limit-up-pool/{date}",
    response_model=List[LimitUpStockResponse],
    responses={
        400: {"model": ErrorResponse, "description": "日期格式错误"},
        500: {"model": ErrorResponse, "description": "内部服务器错误"},
    },
)
async def get_limit_up_pool(date: str):
    """获取涨停股池数据
    
    获取指定日期的涨停股池数据，包含涨停股票的详细信息：
    - 股票基本信息（代码、名称、行业）
    - 价格信息（最新价、涨跌幅）
    - 交易信息（成交额、换手率、市值）
    - 涨停信息（封板时间、炸板次数、连板数等）
    
    数据来源：东方财富网涨停板行情
    """
    try:
        return await stock_service.get_limit_up_pool(date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取涨停股池数据失败: {str(e)}")


@router.post(
    "/limit-up-pool",
    response_model=List[LimitUpStockResponse],
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "内部服务器错误"},
    },
)
async def get_limit_up_pool_post(request: LimitUpPoolRequest):
    """获取涨停股池数据 (POST方式)
    
    通过POST请求获取指定日期的涨停股池数据
    """
    try:
        return await stock_service.get_limit_up_pool(request.date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取涨停股池数据失败: {str(e)}")


@router.get(
    "/strong-pool/{date}",
    response_model=List[StrongStockResponse],
    responses={
        400: {"model": ErrorResponse, "description": "日期格式错误"},
        500: {"model": ErrorResponse, "description": "内部服务器错误"},
    },
)
async def get_strong_stock_pool(date: str):
    """获取强势股池数据
    
    获取指定日期的强势股池数据，包含强势股票的详细信息：
    - 股票基本信息（代码、名称、行业）
    - 价格信息（最新价、涨跌幅、涨停价、涨速）
    - 交易信息（成交额、换手率、市值、量比）
    - 强势信息（是否新高、入选理由、涨停统计等）
    
    数据来源：东方财富网强势股池
    """
    try:
        return await stock_service.get_strong_stock_pool(date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取强势股池数据失败: {str(e)}")


@router.post(
    "/strong-pool",
    response_model=List[StrongStockResponse],
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "内部服务器错误"},
    },
)
async def get_strong_stock_pool_post(request: StrongPoolRequest):
    """获取强势股池数据 (POST方式)
    
    通过POST请求获取指定日期的强势股池数据
    """
    try:
        return await stock_service.get_strong_stock_pool(request.date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取强势股池数据失败: {str(e)}")


@router.get(
    "/sub-new-pool/{date}",
    response_model=List[SubNewStockResponse],
    responses={
        400: {"model": ErrorResponse, "description": "日期格式错误"},
        500: {"model": ErrorResponse, "description": "内部服务器错误"},
    },
)
async def get_sub_new_stock_pool(date: str):
    """获取次新股池数据
    
    获取指定日期的次新股池数据，包含次新股票的详细信息：
    - 股票基本信息（代码、名称、行业）
    - 价格信息（最新价、涨跌幅、涨停价）
    - 交易信息（成交额、转手率、流通市值、总市值）
    - 次新股特有信息（开板几日、开板日期、上市日期、是否新高等）
    
    数据来源：东方财富网次新股池
    """
    try:
        return await stock_service.get_sub_new_stock_pool(date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取次新股池数据失败: {str(e)}")


@router.post(
    "/sub-new-pool",
    response_model=List[SubNewStockResponse],
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "内部服务器错误"},
    },
)
async def get_sub_new_stock_pool_post(request: SubNewPoolRequest):
    """获取次新股池数据 (POST方式)
    
    通过POST请求获取指定日期的次新股池数据
    """
    try:
        return await stock_service.get_sub_new_stock_pool(request.date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取次新股池数据失败: {str(e)}")


@router.get(
    "/explode-board-pool/{date}",
    response_model=List[ExplodeBoardStockResponse],
    responses={
        400: {"model": ErrorResponse, "description": "日期格式错误"},
        500: {"model": ErrorResponse, "description": "内部服务器错误"},
    },
)
async def get_explode_board_stock_pool(date: str):
    """获取炸板股池数据
    
    获取指定日期的炸板股池数据，包含炸板股票的详细信息：
    - 股票基本信息（代码、名称、行业）
    - 价格信息（最新价、涨跌幅、涨停价、涨速）
    - 交易信息（成交额、换手率、流通市值、总市值）
    - 炸板信息（首次封板时间、炸板次数、涨停统计、振幅等）
    
    数据来源：东方财富网炸板股池
    """
    try:
        return await stock_service.get_explode_board_stock_pool(date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取炸板股池数据失败: {str(e)}")


@router.post(
    "/explode-board-pool",
    response_model=List[ExplodeBoardStockResponse],
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "内部服务器错误"},
    },
)
async def get_explode_board_stock_pool_post(request: ExplodeBoardPoolRequest):
    """获取炸板股池数据 (POST方式)
    
    通过POST请求获取指定日期的炸板股池数据
    """
    try:
        return await stock_service.get_explode_board_stock_pool(request.date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取炸板股池数据失败: {str(e)}")


@router.get(
    "/fall-limit-pool/{date}",
    response_model=List[FallLimitStockResponse],
    responses={
        400: {"model": ErrorResponse, "description": "日期格式错误"},
        500: {"model": ErrorResponse, "description": "内部服务器错误"},
    },
)
async def get_fall_limit_stock_pool(date: str):
    """获取跌停股池数据
    
    获取指定日期的跌停股池数据，包含跌停股票的详细信息：
    - 股票基本信息（代码、名称、行业）
    - 价格信息（涨跌幅、最新价、动态市盈率）
    - 交易信息（成交额、换手率、流通市值、总市值）
    - 跌停信息（封单资金、最后封板时间、板上成交额、连续跌停、开板次数等）
    
    数据来源：东方财富网跌停股池
    """
    try:
        return await stock_service.get_fall_limit_stock_pool(date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取跌停股池数据失败: {str(e)}")


@router.post(
    "/fall-limit-pool",
    response_model=List[FallLimitStockResponse],
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "内部服务器错误"},
    },
)
async def get_fall_limit_stock_pool_post(request: FallLimitPoolRequest):
    """获取跌停股池数据 (POST方式)
    
    通过POST请求获取指定日期的跌停股池数据
    """
    try:
        return await stock_service.get_fall_limit_stock_pool(request.date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取跌停股池数据失败: {str(e)}") 