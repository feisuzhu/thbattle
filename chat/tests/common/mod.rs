use std::sync::Once;
use std::time::Duration;

use actix::{Actor, ActorContext, AsyncContext, Context, Handler};
use actix_derive::Message;

use aya::util::init_log as aya_init_log;

static INIT_LOG: Once = Once::new();

pub fn init_log() {
    INIT_LOG.call_once(|| aya_init_log());
}

#[derive(Message)]
struct Tick;

pub struct Chain<T: 'static>(T, Vec<Box<dyn Fn(&mut T) + Send + 'static>>);

impl<T: 'static> Chain<T> {
    pub fn with<F: Fn(&mut T) + Send + 'static>(mut self, f: F) -> Self {
        self.1.push(Box::new(f));
        self
    }

    pub fn fire(self) {
        RunLater::create(|ctx| {
            ctx.notify_later(Tick, Duration::new(0, 10000000));
            RunLater { chain: self }
        });
    }
}

pub struct RunLater<T: 'static> {
    chain: Chain<T>,
}

impl<T: 'static> Actor for RunLater<T> {
    type Context = Context<Self>;
}

impl<T: 'static> Handler<Tick> for RunLater<T> {
    type Result = ();
    fn handle(&mut self, _: Tick, ctx: &mut Self::Context) {
        if self.chain.1.len() > 0 {
            let f = self.chain.1.remove(0);
            f(&mut self.chain.0);
            ctx.notify_later(Tick, Duration::new(0, 10000000));
        } else {
            ctx.stop();
        }
    }
}

pub fn run_later<T: 'static>(ctx: T) -> Chain<T> {
    Chain(ctx, vec![])
}
