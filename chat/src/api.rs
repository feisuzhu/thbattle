use std::num::NonZeroU32;

use actix::prelude::*;
use serde_derive::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Message)]
#[rtype(result = "()")]
pub struct Message {
    pub entity: String,  // "Game:123123" || "Lobby" || "Aya" || "User:123123"
    pub channel: String, // ["player", "observer"] || "" || ["forest", "lake"] || ""
    pub text: Vec<u8>,
    pub sender: Option<NonZeroU32>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Message)]
#[rtype(result = "()")]
#[serde(tag = "op", content = "arg")]
pub enum Request {
    Login { token: String },
    Join { room: String },
    Leave { room: String },
    Message(Message),
    // ----- ADMIN OPS -----
    Kick { user_id: String },
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Message)]
#[rtype(result = "()")]
#[serde(tag = "ev", content = "arg")]
pub enum Event {
    LoginRequired,
    Success,
    Message(Message),
    Undelivered(Message),
    Kicked,
    Error(String),
}
