use std::ops::Deref;
use std::ops::DerefMut;

use crate::model::prelude::*;

#[repr(usize)]
pub enum CardListKind {
    Undefined,
    Deck,
    Dropped,
    Hand,
    Shown,
    Equip,
    Fatetell,
    Special,
}

pub struct PlayerCardsInner {
    pub hand: Vec<Handle>,
    pub shown: Vec<Handle>,
    pub equip: Vec<Handle>,
    pub fatetell: Vec<Handle>,
    pub special: Vec<Handle>,
}

pub struct PlayerCards {
    inner: Box<PlayerCardsInner>,
}

impl Deref for PlayerCards {
    type Target = PlayerCardsInner;

    fn deref(&self) -> &Self::Target {
        &self.inner
    }
}

impl DerefMut for PlayerCards {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.inner
    }
}
