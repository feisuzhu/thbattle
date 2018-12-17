mod weakreg;

use std::io::Write;
use std::thread;

use chrono::prelude::*;
use env_logger;

pub use self::weakreg::*;

pub fn init_log() {
    env_logger::Builder::from_env("AYA_LOG")
        .format(|buf, record| {
            writeln!(
                buf,
                "[{} {} {:?} {}:{}] {}",
                &record.level().to_string()[..1],
                Local::now().format("%Y%m%d %H:%M:%S"),
                thread::current().id(),
                // record.module_path().unwrap_or("?"),
                record.file().unwrap_or("?"),
                record.line().unwrap_or(0),
                record.args(),
            )
        })
        .init();
}
