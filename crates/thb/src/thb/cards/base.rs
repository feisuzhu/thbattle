pub enum Suit {
    Undecided,
    Spade,
    Heart,
    Club,
    Diamond,
}

pub enum Color {
    Undecided,
    Black,
    Red,
}

pub type Rank = u16;

pub const A: Rank = 1;
pub const J: Rank = 11;
pub const Q: Rank = 12;
pub const K: Rank = 13;

pub struct CardIdentity {
    suit: Suit,
    rank: Rank,
}
