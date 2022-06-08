use aya::util::init_log as aya_init_log;
use std::sync::Once;

static INIT_LOG: Once = Once::new();

pub fn init_log() {
    INIT_LOG.call_once(|| aya_init_log());
}
