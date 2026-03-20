#!lua name=aihub_rate_limits

--[[
Atomically checks all limits and increments all counters only if none are exceeded.

KEYS: Redis counter keys (one per limit)
ARGV: For each key i: ARGV[2*i - 1] = limit, ARGV[2*i] = ttl_seconds

Return format: {exceeded_flag, count1, ttl1, count2, ttl2, ...}
  exceeded_flag = 1 if any limit is at or above its max, 0 otherwise
  ttl values are the remaining TTL in seconds for each key
]]

local function check_and_increment(keys, args)
    local n = #keys
    local counts = {}
    local exceeded = 0

    -- Phase 1: read all counters and check limits
    for i = 1, n do
        local raw = redis.call('GET', keys[i])
        local count = raw and tonumber(raw) or 0
        counts[i] = count
        local limit = tonumber(args[2 * i - 1])
        if count >= limit then
            exceeded = 1
        end
    end

    -- Phase 2: increment all counters only if none exceeded
    if exceeded == 0 then
        for i = 1, n do
            local ttl = tonumber(args[2 * i])
            local new_count = redis.call('INCR', keys[i])
            if new_count == 1 or redis.call('TTL', keys[i]) <= 0 then
                redis.call('EXPIRE', keys[i], ttl)
            end
            counts[i] = new_count
        end
    end

    -- Return exceeded flag followed by interleaved counts and TTLs
    local result = {exceeded}
    for i = 1, n do
        result[#result + 1] = counts[i]
        result[#result + 1] = redis.call('TTL', keys[i])
    end
    return result
end

redis.register_function('aihub_check_and_increment', check_and_increment)
