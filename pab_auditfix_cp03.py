"""CP03: restore the deathtouch granted by Infuse with Vitality.

The preexisting S15 `infused_eot` registry already denotes spell resolution and
expires at each cleanup; no new card state or changes to frozen source needed.
Both controllers can have an infused attacker/blocker.
"""
from pab_auditfix_cp02 import AuditFixCP02Mixin

class AuditFixCP03Mixin(AuditFixCP02Mixin):
    def _deathtouch(self, permanent):
        if permanent.creature and permanent.uid in self.infused_eot:
            return True
        return super()._deathtouch(permanent)
