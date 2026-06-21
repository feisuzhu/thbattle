use crate::model::prelude::*;

pub struct Damage {
    pub amount: u32,
}

impl Action for Damage {
    fn apply(&self, g: &mut Game) -> Result<bool> {}

    fn is_valid(&self, g: &mut Game, act: Handle) -> Result<bool> {}
}
