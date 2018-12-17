use lazy_static::lazy_static;

use crate::actors::{Room, Session};
use crate::util::WeakRegistry;

lazy_static! {
    pub static ref SESSIONS: WeakRegistry<Session> = WeakRegistry::new();
    pub static ref ROOMS: WeakRegistry<Room> = WeakRegistry::new();
}
