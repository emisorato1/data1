"""Redis-backed token bucket algorithm for rate limiting."""

import time

from redis.asyncio import Redis

# Lua script to atomically:
# 1. Fetch current tokens and last refresh time.
# 2. Refill tokens based on time elapsed * rate.
# 3. Cap at max_capacity (burst limit).
# 4. Check if enough tokens to consume.
# 5. If allowed, deduct tokens and save state.
# 6. Return (allowed (1/0), tokens_remaining, reset_time_seconds).

LUA_RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local bucket = redis.call("HMGET", key, "tokens", "last_update")
local current_tokens = bucket[1] and tonumber(bucket[1]) or capacity
local last_update = bucket[2] and tonumber(bucket[2]) or now

local time_passed = math.max(0, now - last_update)
local new_tokens = math.min(capacity, current_tokens + (time_passed * rate))

local allowed = 0

if new_tokens >= requested then
    allowed = 1
    new_tokens = new_tokens - requested

    redis.call("HMSET", key, "tokens", new_tokens, "last_update", now)

    local expire_time = math.ceil((capacity - new_tokens) / rate)
    if expire_time > 0 then
        redis.call("EXPIRE", key, expire_time)
    end
end

local remaining = math.floor(new_tokens)
local reset_in_seconds = 0
if allowed == 0 then
    reset_in_seconds = math.ceil((requested - new_tokens) / rate)
else
    reset_in_seconds = math.ceil((capacity - new_tokens) / rate)
end

return {allowed, remaining, reset_in_seconds}
"""


class TokenBucket:
    """Token bucket rate limiter backed by Redis Lua script."""

    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        # Register the script with Redis connection
        self._script = self.redis.register_script(LUA_RATE_LIMIT_SCRIPT)

    async def consume(
        self,
        key: str,
        capacity: int,
        rate: float,
        requested: int = 1,
    ) -> tuple[bool, int, int]:
        """Attempt to consume tokens from the bucket.

        Args:
            key: Redis key for the bucket (e.g. "rl:tb:chat:user123").
            capacity: Maximum bucket size (burst size).
            rate: Token refill rate per second.
            requested: Number of tokens to consume.

        Returns:
            Tuple containing:
            - allowed: True if request is allowed, False if throttled.
            - remaining: Number of tokens remaining in the bucket (int).
            - reset_in: Seconds until bucket is fully refilled (if allowed) or until \\
              enough tokens are available (if not allowed).
        """
        now = time.time()

        # Run Lua script atomically
        # Script returns list of [allowed, remaining, reset_in_seconds]
        result = await self._script(keys=[key], args=[capacity, rate, now, requested])

        allowed = bool(result[0])
        remaining = int(result[1])
        reset_in = int(result[2])

        return allowed, remaining, reset_in
