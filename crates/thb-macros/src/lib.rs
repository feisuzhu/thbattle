mod derive_anycast;
mod with_macro;

use proc_macro::TokenStream;

/// Derive macro implementing `Anycast` for a struct, enum or union.
///
/// Adapted from trait-cast-rs (https://github.com/ink-feather-org/trait-cast-rs)
/// Licensed under MIT OR Apache-2.0
///
/// Use `#[anycast(SomeTrait, ...)]` to specify all possible target traits
/// for which trait objects can be downcast from `dyn Anycast`.
///
/// Example:
/// ```ignore
/// use thb::Anycast;
///
/// #[derive(Anycast)]
/// #[anycast(Print)]
/// struct Source(i32);
///
/// trait Print {
///     fn print(&self) -> i32;
/// }
/// impl Print for Source {
///     fn print(&self) -> i32 { self.0 }
/// }
/// ```
#[proc_macro_derive(Anycast, attributes(anycast))]
pub fn derive_anycast(input: TokenStream) -> TokenStream {
    derive_anycast::derive_anycast(input)
}

/// The `with!` proc macro provides ergonomic access to `GameObject` components
/// through the `ObjectArena`.
///
/// Syntax:
/// ```ignore
/// with!(arena_owner, |binding1, binding2, ...| { body })
/// ```
///
/// Each binding can be:
/// - `name` — bind as `&mut GameObject`
/// - `name: Type` — bind as `&mut Type` via `.need::<Type>()`
/// - `name: *Type` — copy the component via deref
/// - `name: @handle` — bind a specific handle's `GameObject`
/// - `name: Type @handle` — bind component `Type` from a specific handle
/// - `name: *Type @handle` — copy component `Type` from a specific handle
#[proc_macro]
pub fn with(input: TokenStream) -> TokenStream {
    with_macro::with(input)
}
