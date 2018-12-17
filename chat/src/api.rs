use actix_derive::Message;
use serde_derive::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct User {
    pub id: String,
    pub name: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Message)]
pub struct Message {
    pub entity: String,  // "Game:123123" || "Lobby" || "Aya" || "User:123123"
    pub channel: String, // ["player", "observer"] || "" || ["forest", "lake"] || ""
    pub text: String,
    pub sender: Option<User>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Message)]
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
#[serde(tag = "ev", content = "arg")]
pub enum Event {
    LoginRequired,
    Success,
    Message(Message),
    Undelivered(Message),
    Kicked,
    Error(String),
}
