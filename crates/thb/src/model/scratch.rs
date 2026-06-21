/*
 * -- actions
 * Class{name, {Action or Card or Skill}}
 * Source
 * Targeted
 * Cards { lst, usage }
 * Basic / Spellcard
 * xxx impls Action + AskForAction + xxx {...}
 *
 * -- for cards
 * Class{name, {Action or Card or Skill}}
 * Physical / Virtual
 * CardCategory {
 *     Basic
 *     InstantSpellcard
 *     DelayedSpellcard
 *     Equipment
 * }
 * <equipment-tags>:
 *     Weapon{range}
 *     RedUFO{dist}
 *     GreenUFO{dist}
 *     Shield{}
 *     Accessories{}
 * IntentedTargets (One, OtherOne, ...)
 * // only for live cards
 * CardIdentity { suit, rank }
 * Synchronized(sid) == sync_id
 * Entity(id) == legacy track_id
 * Cards { lst, usage } == legacy associated_cards
 *
 * -- for players
 * Player {...}
 * Character {...}
 * Life { life, maxlife, dead }
 * Skills { ... }
 * Tags { BTreeMap<&'static str, &'static str> }
 * PlayerCards { Box<hand, shown, equip, fatetell, special: Vec<Handle>> }
 */

// use std::any::Any;

// fn foo() {
//     use std::collections::BTreeMap;
//     use std::collections::Vec;
//     let a: BTreeMap<&str, &str> = todo!();
//     let b: Vec<&str> = todo!();
// }
