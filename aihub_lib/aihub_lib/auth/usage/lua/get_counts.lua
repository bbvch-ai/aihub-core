#!lua name=aihub_rate_limits_read

--[[
Atomically reads all counter values and their TTLs.

KEYS: Redis counter keys (one per limit)
ARGV: (none)

Return format: {count1, ttl1, count2, ttl2, ...}
]]

local function get_counts(keys, args)
    local result = {}
    for i = 1, #keys do
        local raw = redis.call('GET', keys[i])
        local count = raw and tonumber(raw) or 0
        result[#result + 1] = count
        result[#result + 1] = redis.call('TTL', keys[i])
    end
    return result
end

redis.register_function('aihub_get_counts', get_counts)
