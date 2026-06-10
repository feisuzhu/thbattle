use std::fmt;

/// A player in the game.
///
/// Game-specific data (character, skills, hand) lives in the game mode's
/// own types, keyed by [`PlayerId`]. This keeps the core engine decoupled
/// from mode specifics.
#[derive(Clone)]
pub struct Player {
    pub pid: u32,
}

impl Player {
    pub fn new(pid: PlayerId, name: impl Into<String>) -> Self {
        Self {
            pid,
            name: name.into(),
        }
    }
}

impl fmt::Debug for Player {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "P{}:{}", self.pid, self.name)
    }
}

impl fmt::Display for Player {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.name)
    }
}
