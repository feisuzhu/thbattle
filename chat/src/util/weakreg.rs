use std::hash::Hash;

use actix::{Actor, Addr, WeakAddr};
use chashmap::CHashMap;

#[derive(Debug)]
pub struct WeakRegistry<A: Actor, K: Hash + Eq = String> {
    hm: CHashMap<K, WeakAddr<A>>,
}

pub trait WeakRegistryDefault<A: Actor, K: Hash + Eq = String> {
    fn new(key: &K) -> Addr<A>;
}

impl<A: Actor, K: Hash + Eq + Clone> WeakRegistry<A, K> {
    pub fn new() -> Self {
        Self {
            hm: CHashMap::new(),
        }
    }

    pub fn register(&self, key: K, addr: &Addr<A>) {
        self.hm.insert(key, addr.downgrade());
    }

    pub fn query(&self, key: &K) -> Option<Addr<A>> {
        self.hm.get(key)?.upgrade()
    }

    #[allow(dead_code)]
    pub fn remove(&self, key: &K) {
        self.hm.remove(key);
    }

    pub fn get(&self, key: &K) -> Addr<A>
    where
        A: WeakRegistryDefault<A, K>,
    {
        match self.query(key) {
            Some(a) => a,
            None => {
                let a = A::new(key);
                self.hm.insert(key.clone(), a.downgrade());
                a
            }
        }
    }
}
