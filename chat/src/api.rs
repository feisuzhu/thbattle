use std::num::NonZeroU32;

use actix::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Message)]
#[rtype(result = "()")]
pub struct Message {
    pub entity: String,  // "Game:123123" || "Lobby" || "Aya" || "User:123123"
    pub channel: String, // ["player", "observer"] || "" || ["forest", "lake"] || ""
    #[serde(with = "serde_bytes")]
    pub text: Vec<u8>,
    #[serde(skip_deserializing)]
    pub sender: Option<NonZeroU32>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Message)]
#[rtype(result = "()")]
pub struct Login {
    pub token: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Message)]
#[rtype(result = "()")]
pub struct Join {
    pub room: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Message)]
#[rtype(result = "()")]
pub struct Leave {
    pub room: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Message)]
#[rtype(result = "()")]
pub struct Kick {
    pub uid: NonZeroU32,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Message)]
#[rtype(result = "()")]
#[serde(tag = "op", content = "arg")]
pub enum Request {
    Login(Login),
    Join(Join),
    Leave(Leave),
    Message(Message),
    // ----- ADMIN OPS -----
    Kick(Kick),
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

// -------------------------
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct GraphQLRequest<T> {
    pub query: String,
    pub variables: T,
    pub strip: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct GraphQLError {
    pub message: String,
    pub path: Option<Vec<String>>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct GraphQLResponse<T> {
    pub data: T,
    pub errors: Option<Vec<GraphQLError>>,
}
