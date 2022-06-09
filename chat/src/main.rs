mod actors;
mod api;
mod core;
mod util;

use std::sync::Arc;

use argparse::{ArgumentParser, Store};

use crate::core::ChatServerCore;

// #[derive(Clone)]
// pub struct AyaState {
//     pub backend: String,
// }

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    util::init_log();

    let mut backend = "http://localhost:8000/graphql-msgpack".to_string();
    let mut listen = "0.0.0.0:7777".to_string();

    {
        let mut parser = ArgumentParser::new();
        parser
            .refer(&mut backend)
            .add_option(&["--backend"], Store, "");
        parser
            .refer(&mut listen)
            .add_option(&["--listen"], Store, "");
        parser.parse_args_or_exit();
    }

    let core = Arc::new(ChatServerCore {
        backend,
        listen,
        sessions: Default::default(),
        rooms: Default::default(),
    });

    core.serve().await
}
