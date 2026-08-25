--[[
Hands a mailbox lease back only while this run still holds it.

KEYS[1]: the lease key
ARGV[1]: the run id claiming to hold it

Returns 1 when the lease was released, 0 when it is held by someone else or has already expired.

This is the dangerous half of the same race the renewal script closes. A GET, a comparison in Python and
then a DEL lets a run whose lease lapsed between the two delete the lease its successor has since
acquired — handing the mailbox to a third run while the second is still filing it, which is exactly the
double-filing the lease exists to prevent.
]]

if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
