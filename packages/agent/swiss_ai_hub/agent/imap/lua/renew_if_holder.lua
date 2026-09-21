--[[
Extends a mailbox lease only while this run still holds it.

KEYS[1]: the lease key
ARGV[1]: the run id claiming to hold it
ARGV[2]: the new TTL in seconds

Returns 1 when the lease was extended, 0 when it is held by someone else or has already expired.

Compare and extend have to happen in one round trip: a GET, a comparison in Python and then an EXPIRE
leaves a window in which the lease lapses and a second run acquires it, so the first run's EXPIRE would
extend the successor's lease using the loser's TTL.
]]

if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('EXPIRE', KEYS[1], ARGV[2])
end
return 0
