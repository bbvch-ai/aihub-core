--[[
Takes a mailbox lease back when it is ours or unclaimed, and refuses only when another run holds it.

KEYS[1]: the lease key
ARGV[1]: the run id reclaiming it
ARGV[2]: the TTL in seconds

Returns 1 when the lease is now ours, 0 when another run holds it.

Deliberately more permissive than renew_if_holder: this is the only place a run may take back a lease it
already let lapse. See MailboxRunLease.reacquire for why that is safe after the mail has been filed, and
why it must not be used before.

One round trip for the same reason as the other two scripts: reading the holder into Python and then
setting leaves a window in which a second run acquires between the two, and the SET would then steal a
mailbox that run is actively working.
]]

local holder = redis.call('GET', KEYS[1])
if holder and holder ~= ARGV[1] then
    return 0
end
redis.call('SET', KEYS[1], ARGV[1], 'EX', ARGV[2])
return 1
