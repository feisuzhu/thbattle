use crate::model::prelude::*;
use crate::thb::cards::base::{Rank, Suit};

pub struct Attack;
pub struct AttackCard;

impl Action for Attack {
    fn apply(&self, g: &mut Game) -> Result<bool> {
        Ok(true)
    }
    fn is_valid(&self, g: &mut Game, act: Handle) -> Result<bool> {
        Ok(true)
    }
}

impl AttackCard {
    pub fn definition(suit: Suit, rank: Rank) -> GameObject {
        GameObject::new()
    }
}
