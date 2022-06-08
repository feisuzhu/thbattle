use std::num::NonZeroU32;

use actix::Addr;
use chashmap::CHashMap;
use lazy_static::lazy_static;

use crate::actors::{Room, Session};

lazy_static! {
    pub static ref SESSIONS: CHashMap<NonZeroU32, Addr<Session>> = CHashMap::new();
    pub static ref ROOMS: CHashMap<String, Addr<Room>> = CHashMap::new();
}
