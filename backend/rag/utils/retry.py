import time
import asyncio
import logging
from typing import Callable, TypeVar, Any
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
    max_total_time: float = 60.0  # 최대 총 재시도 시간 (초)
):
    """
    재시도 로직이 포함된 데코레이터
    
    Args:
        max_retries: 최대 재시도 횟수
        initial_delay: 초기 지연 시간 (초)
        max_delay: 최대 지연 시간 (초)
        exponential_base: 지수 백오프 베이스
        exceptions: 재시도할 예외 타입들
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            import time
            delay = initial_delay
            last_exception = None
            start_time = time.time()
            
            for attempt in range(max_retries):
                # 최대 총 시간 체크
                elapsed = time.time() - start_time
                if elapsed > max_total_time:
                    logger.error(
                        f"{func.__name__} 최대 재시도 시간 초과 ({max_total_time}초). "
                        f"시도 횟수: {attempt + 1}/{max_retries}"
                    )
                    if last_exception:
                        raise TimeoutError(
                            f"최대 재시도 시간({max_total_time}초)을 초과했습니다. "
                            f"마지막 오류: {str(last_exception)}"
                        ) from last_exception
                    raise TimeoutError(f"최대 재시도 시간({max_total_time}초)을 초과했습니다.")
                
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        # 남은 시간 체크
                        remaining_time = max_total_time - (time.time() - start_time)
                        if remaining_time < delay:
                            logger.warning(
                                f"{func.__name__} 재시도 시간 부족. 남은 시간: {remaining_time:.2f}초"
                            )
                            break
                        
                        logger.warning(
                            f"{func.__name__} 실패 (시도 {attempt + 1}/{max_retries}): {str(e)}. "
                            f"{delay:.2f}초 후 재시도..."
                        )
                        await asyncio.sleep(delay)
                        delay = min(delay * exponential_base, max_delay)
                    else:
                        logger.error(
                            f"{func.__name__} 최종 실패 (시도 {max_retries}회): {str(e)}"
                        )
            
            if last_exception:
                raise last_exception
            raise TimeoutError(f"{func.__name__} 최대 재시도 횟수 초과")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"{func.__name__} 실패 (시도 {attempt + 1}/{max_retries}): {str(e)}. "
                            f"{delay:.2f}초 후 재시도..."
                        )
                        time.sleep(delay)
                        delay = min(delay * exponential_base, max_delay)
                    else:
                        logger.error(
                            f"{func.__name__} 최종 실패 (시도 {max_retries}회): {str(e)}"
                        )
            
            raise last_exception
        
        # 비동기 함수인지 확인
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

