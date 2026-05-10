# Major Code Convention Changes Compared To Python Version
- Action is pushed onto action_stack and hybrid_stack before ActionBefore rather than ActionApply, this changes behavior of code accessing self.action_stack[-1] in action_before handler, should take this into consideration when migrating.
