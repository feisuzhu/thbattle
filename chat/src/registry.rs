use std::num::NonZeroU32;

use lazy_static::lazy_static;

use crate::actors::{Room, Session};
use crate::util::WeakRegistry;

lazy_static! {
    pub static ref SESSIONS: WeakRegistry<Session, NonZeroU32> = WeakRegistry::new();
    pub static ref ROOMS: WeakRegistry<Room> = WeakRegistry::new();
}
